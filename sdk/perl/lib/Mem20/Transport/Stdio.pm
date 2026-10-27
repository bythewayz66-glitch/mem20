package Mem20::Transport::Stdio;
use strict;
use warnings;

use IPC::Open3 ();
use JSON::PP ();
use POSIX ();
use Symbol qw(gensym);
use Time::HiRes qw(time sleep);
use IO::Select;
use Fcntl ();
use Cwd ();

use Mem20::Errors;
use Mem20::Version ();

# JSON-RPC 2.0 over newline-delimited stdio -- the transport the mem20 server
# exposes (MCP revision 2025-06-18).
#
# One instance owns one child process and serialises access to it with a
# non-blocking select loop, so a single client can be shared across a program
# without interleaving request/response pairs.
#
# Deadlock note: stdout and stderr are both watched by the same loop. Reading
# stdout only would deadlock the moment the server filled its stderr pipe
# buffer (a verbose server would block writing stderr, so it would stop
# writing stdout, and we would sit waiting for a reply that can never come),
# so stderr is always drained on every pass and kept as a bounded tail for
# error messages.
#
# stderr is put in O_NONBLOCK mode. Draining it opportunistically (e.g. while
# composing a timeout message) must never block: a blocking read parks until
# the child writes again, which turns an error path into a hang. See
# sdk/perl/AUDIT.md, finding T1.

my $JSONRPC_VERSION  = '2.0';
my $STDERR_TAIL_MAX  = 4000;
my $MAX_LINE_BYTES   = 8 * 1024 * 1024;

sub new {
    my ($class, %args) = @_;
    my $config = $args{config}
        or Mem20::ConfigurationError->throw(message => 'transport requires a config');

    my $self = bless {
        config       => $config,
        pid          => undef,
        stdin        => undef,
        stdout       => undef,
        stderr       => undef,
        next_id      => 0,
        buffer       => '',
        pending      => [],     # complete lines not yet consumed
        stderr_tail  => '',
        session      => undef,
        closed       => 0,
        surface      => undef,  # name => inputSchema, filled by tools/list
    }, $class;

    $self->_start_process;
    return $self;
}

sub pid     { $_[0]{pid} }
sub config  { $_[0]{config} }
sub session { $_[0]{session} }

# Send a request and wait for the matching response. Returns the `result`
# member; throws Mem20::ToolError on a JSON-RPC error object and
# Mem20::TransportError on a timeout, a dead child, or unparseable output.
sub request {
    my ($self, $method, $params) = @_;
    $params //= {};

    # MCP requires `initialize` before any other request: a server answers
    # tools/list or tools/call sent first with -32602 "Invalid request
    # parameters". connect() used to be the only thing that performed the
    # handshake, so every caller that trusted the documented "calls connect on
    # demand" behaviour got a protocol error on its first tool call. Doing it
    # here makes the handshake lazy but unconditional; initialize itself is
    # exempt so this cannot recurse.
    $self->initialize_session if $method ne 'initialize' && !$self->{session};

    $self->_ensure_alive;

    my $id = ++$self->{next_id};
    $self->_write_message( id => $id, method => $method, params => $params );

    return $self->_read_response($id);
}

# Fire-and-forget notification: no id, no reply expected.
sub notify {
    my ($self, $method, $params) = @_;
    $params //= {};

    $self->_ensure_alive;
    $self->_write_message( method => $method, params => $params );
    return;
}

# Perform the MCP initialize handshake once, before any tool call. Returns a
# hashref with protocol_version / server_info / capabilities.
sub initialize_session {
    my ($self) = @_;
    return $self->{session} if $self->{session};

    my $result = $self->request(
        'initialize',
        {
            protocolVersion => $self->{config}->protocol_version,
            capabilities    => {},
            clientInfo      => {
                name    => 'mem20-sdk-perl',
                version => $Mem20::Version::VERSION,
            },
        }
    );

    $self->notify( 'notifications/initialized', {} );

    $self->{session} = {
        protocol_version => $result->{protocolVersion},
        server_info      => $result->{serverInfo}     || {},
        capabilities     => $result->{capabilities}   || {},
    };
    return $self->{session};
}

sub close {
    my ($self) = @_;
    return if $self->{closed};
    $self->{closed} = 1;

    if (defined $self->{stdin}) {
        eval { close $self->{stdin} };
    }

    if (defined $self->{pid} && $self->{pid} > 0) {
        # SIGTERM, then a short grace period, then SIGKILL, then reap. Zombies
        # are cheap but a leaked child that still holds the store's lock is not.
        eval { kill 'TERM', $self->{pid} };

        for (1 .. 20) {
            my $reaped = waitpid($self->{pid}, POSIX::WNOHANG());
            last if $reaped != 0;
            sleep 0.05;
        }

        if (waitpid($self->{pid}, POSIX::WNOHANG()) == 0) {
            eval { kill 'KILL', $self->{pid} };
            eval { waitpid($self->{pid}, 0) };
        }
    }

    $self->{pid}         = undef;
    $self->{session}     = undef;
    $self->{stdin}       = undef;
    $self->{stdout}      = undef;
    $self->{stderr}      = undef;
    $self->{buffer}      = '';
    $self->{pending}     = [];
    $self->{surface}     = undef;
    return;
}

sub DESTROY {
    my ($self) = @_;
    local $@;
    eval { $self->close };
    return;
}

# ---------------------------------------------------------------- internals

sub _start_process {
    my ($self) = @_;

    my $config = $self->{config};
    my $argv    = [ @{ $config->server_command } ];

    my $err_fh = gensym;

    # Env is passed through explicitly so MEM20_* overrides reach the child
    # without mutating the parent's %ENV for the rest of the program.
    local %ENV = ( %ENV, %{ $config->child_env } );

    # The server is run as a script (`python mcp/mcp_server.py`) and imports its
    # siblings by script-directory name, so it must be exec'd with the checkout
    # as its working directory. cwd() was documented but never applied, which
    # made every relative `server_command` resolve against the CALLER's
    # directory: the child died at startup with
    # "can't open file '<caller>/mcp_server.py'".
    my $cwd = $config->cwd;
    if ( defined $cwd && length $cwd ) {
        if ( !-d $cwd ) {
            Mem20::TransportError->throw(
                message => "configured cwd '$cwd' is not a directory "
                    . '(it must be the mem20 checkout containing mcp/)'
            );
        }
    }

    # chdir is process-global, so it must be undone: leaving the SDK pointing at
    # the checkout would silently relocate every relative path the CALLER opens
    # afterwards. Save and restore around the spawn only.
    my $prev_cwd = Cwd::getcwd();
    if ( defined $cwd && length $cwd ) {
        chdir $cwd or Mem20::TransportError->throw(
            message => "could not chdir to configured cwd '$cwd': $!"
        );
    }

    my ($pid, $in_fh, $out_fh);

    my $ok = eval {
        $pid = IPC::Open3::open3( $in_fh, $out_fh, $err_fh, @$argv );
        1;
    };
    my $spawn_err = $@;

    if ( defined $prev_cwd && length $prev_cwd ) {
        chdir $prev_cwd;
    }

    if (!$ok || !$pid) {
        my $why = $spawn_err || 'open3 returned no pid';
        chomp $why;
        Mem20::TransportError->throw(
            message => 'failed to start mem20 server ('
                . join(' ', @$argv) . "): $why"
        );
    }

    $self->{pid}    = $pid;
    $self->{stdin}  = $in_fh;
    $self->{stdout} = $out_fh;
    $self->{stderr} = $err_fh;

    binmode $self->{stdin};
    binmode $self->{stdout};
    binmode $self->{stderr};

    # stderr must never block. _drain_stderr is called from error paths (a
    # timeout, a dead child) where the child may be idle or wedged; a blocking
    # sysread there waits forever and the "error" becomes a hang.
    my $flags = fcntl( $self->{stderr}, Fcntl::F_GETFL(), 0 );
    if (defined $flags) {
        eval { fcntl( $self->{stderr}, Fcntl::F_SETFL(), $flags | Fcntl::O_NONBLOCK() ) };
    }

    # Buffering off on stdin: a buffered write would sit in our buffer instead
    # of reaching the server, and the reply would never come.
    my $old = select $self->{stdin};
    $| = 1;
    select $old;

    return;
}

sub _write_message {
    my ($self, %payload) = @_;

    my $json = eval {
        JSON::PP->new->utf8->canonical->encode({ jsonrpc => $JSONRPC_VERSION, %payload });
    };
    if ($@) {
        my $why = $@;
        chomp $why;
        Mem20::TransportError->throw(message => "could not encode request: $why");
    }

    my $fh = $self->{stdin}
        or Mem20::TransportError->throw(message => 'mem20 server stdin is closed');

    my $ok = eval { print {$fh} "$json\n"; 1 };
    if (!$ok) {
        my $why = $@ || $!;
        chomp $why;
        Mem20::TransportError->throw(
            message => "mem20 server closed the stdio pipe: $why (" . $self->_stderr_tail . ')'
        );
    }
    return;
}

# Pull every complete newline-terminated line out of the read buffer. Handles
# the case where one sysread returns several responses, or the tail of one
# response plus the whole of the next.
sub _extract_lines {
    my ($self) = @_;

    while ( $self->{buffer} =~ s/\A([^\n]*)\n// ) {
        my $line = $1;
        $line =~ s/\r\z//;
        next if $line =~ /^\s*$/;
        push @{ $self->{pending} }, $line;
    }

    # A frame that never terminates would grow without bound; a server that
    # wrote a partial frame and died is indistinguishable from one still
    # composing a gigantic reply, so cap it rather than exhaust memory.
    if ( length $self->{buffer} > $MAX_LINE_BYTES ) {
        my $got = length $self->{buffer};
        $self->{buffer} = '';
        Mem20::TransportError->throw(
            message => "mem20 server sent a single line of $got bytes "
                . "without a terminator (limit $MAX_LINE_BYTES)"
        );
    }
    return;
}

# Read one response, skipping notifications and replies to other ids. Blocks
# until the deadline, draining stderr as it goes.
sub _read_response {
    my ($self, $id) = @_;

    my $timeout  = $self->{config}->timeout;
    my $deadline = time + $timeout;

    my $select = IO::Select->new( $self->{stdout}, $self->{stderr} );

    while (1) {
        # Serve any complete line already buffered before blocking.
        $self->_extract_lines;
        while ( @{ $self->{pending} } ) {
            my $line    = shift @{ $self->{pending} };
            my $message = $self->_parse_line($line);

            next unless defined $message->{id} && "$message->{id}" eq "$id";

            if (exists $message->{result}) {
                return $message->{result};
            }

            my $error = $message->{error} || {};
            Mem20::ToolError->throw(
                message => $error->{message} || 'mem20 tool call failed',
                code    => $error->{code},
                data    => $error->{data},
            );
        }

        my $remaining = $deadline - time;
        if ($remaining <= 0) {
            my $tail = $self->_stderr_tail;
            Mem20::TransportError->throw(
                message => "timed out after ${timeout}s waiting for response to request #$id"
                    . ( length $tail ? " ($tail)" : '' )
            );
        }

        my @ready = $select->can_read($remaining);
        if (!@ready) {
            next;    # loop re-checks the deadline and throws
        }

        for my $fh (@ready) {
            my $chunk = '';
            my $n = sysread($fh, $chunk, 65536);

            if (!defined $n) {
                next if $!{EINTR} || $!{EAGAIN};
                my $why = $!;
                Mem20::TransportError->throw(message => "read error from mem20 server: $why");
            }

            if ($n == 0) {
                # EOF on either pipe. stdout closing is fatal; stderr closing
                # alone just means the child went quiet.
                if ($fh == $self->{stdout}) {
                    my $tail = $self->_stderr_tail;
                    Mem20::TransportError->throw(
                        message => 'mem20 server closed stdout'
                            . ( length $tail ? " ($tail)" : '' )
                    );
                }
                $select->remove($fh);
                next;
            }

            if ($fh == $self->{stderr}) {
                $self->_append_stderr($chunk);
                next;
            }

            $self->{buffer} .= $chunk;
        }
    }
}

sub _parse_line {
    my ($self, $line) = @_;

    my $message = eval { JSON::PP->new->utf8->decode($line) };
    if ($@ || ref $message ne 'HASH') {
        my $why = $@ || 'decoded to a non-object';
        chomp $why;
        Mem20::TransportError->throw(
            message => "invalid JSON from mem20 server: $why (got: "
                . substr($line, 0, 200) . ')'
        );
    }
    return $message;
}

sub _append_stderr {
    my ($self, $chunk) = @_;
    $self->{stderr_tail} .= $chunk;
    if (length $self->{stderr_tail} > $STDERR_TAIL_MAX) {
        $self->{stderr_tail} = substr($self->{stderr_tail}, -$STDERR_TAIL_MAX);
    }
    return;
}

# Opportunistic, NON-BLOCKING drain used when composing an error message
# mid-call. Bounded by iteration count so a firehose stderr cannot spin here
# forever either.
sub _drain_stderr {
    my ($self) = @_;
    return unless $self->{stderr};

    for (1 .. 64) {
        my $chunk = '';
        my $n = sysread( $self->{stderr}, $chunk, 4096 );
        last if !defined $n || $n == 0;
        $self->_append_stderr($chunk);
    }
    return;
}

sub _stderr_tail {
    my ($self) = @_;
    $self->_drain_stderr;
    my $tail = $self->{stderr_tail} // '';
    $tail =~ s/\s+\z//;
    return $tail;
}

sub _ensure_alive {
    my ($self) = @_;
    return if $self->{closed};

    if (defined $self->{pid}) {
        my $reaped = waitpid($self->{pid}, POSIX::WNOHANG());
        if ($reaped == $self->{pid} || $reaped == -1) {
            $self->{pid} = undef;
            my $tail = $self->_stderr_tail;
            Mem20::TransportError->throw(
                message => 'mem20 server process has exited'
                    . ( length $tail ? " ($tail)" : '' )
            );
        }
    }
    return;
}

1;
__END__

=head1 NAME

Mem20::Transport::Stdio - JSON-RPC 2.0 over stdio for the mem20 server

=head1 SYNOPSIS

    use Mem20::Transport::Stdio;

    my $t = Mem20::Transport::Stdio->new(config => $cfg);
    my $session = $t->initialize_session;
    my $out = $t->request('tools/list', {});
    $t->close;

=head1 DESCRIPTION

Owns one child process and speaks newline-delimited JSON-RPC 2.0 to it. Both
stdout B<and> stderr are watched in the same select loop: draining only stdout
deadlocks as soon as the server fills its stderr pipe buffer (the server blocks
writing stderr, stops writing stdout, and the client waits forever). The last
few KB of stderr are retained and appended to every transport error, because a
bare "closed stdout" is useless on its own.

stderr is held in C<O_NONBLOCK> mode so the opportunistic drain performed while
building an error message can never block. Without that, a timeout whose child
had gone idle turned into an indefinite hang instead of a
C<Mem20::TransportError>.

C<cwd> is applied for the duration of the spawn and then restored, because
C<chdir> is process-global and the caller's relative paths must keep resolving
where they did before.

=head1 METHODS

=over 4

=item C<< new(config => $cfg) >>

=item C<< request($method, \%params) >> - returns C<result>; throws on an error object.
The MCP handshake is performed automatically for any method except
C<initialize>.

=item C<< notify($method, \%params) >> - notification, no reply.

=item C<initialize_session> - idempotent MCP handshake.

=item C<close> - SIGTERM, grace period, SIGKILL, reap.

=item C<pid>, C<session>, C<config>

=back

=head1 LIMITS

A single stdout line is capped at 8 MiB. A server that emits a partial frame
and then dies leaves an unterminated buffer; past the cap the transport throws
instead of growing the buffer until the process is out of memory.

=cut
