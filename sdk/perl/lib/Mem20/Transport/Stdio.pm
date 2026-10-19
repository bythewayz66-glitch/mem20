package Mem20::Transport::Stdio;
use strict;
use warnings;

use IPC::Open3 ();
use JSON::PP ();
use POSIX ();
use Symbol qw(gensym);
use Time::HiRes qw(time sleep);
use IO::Select;

use Mem20::Errors;
use Mem20::Version ();

# JSON-RPC 2.0 over newline-delimited stdio — the transport the mem20 server
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

my $JSONRPC_VERSION = '2.0';
my $STDERR_TAIL_MAX = 4000;

sub new {
    my ($class, %args) = @_;
    my $config = $args{config}
        or Mem20::ConfigurationError->throw(message => 'transport requires a config');

    my $self = bless {
        config      => $config,
        pid         => undef,
        stdin       => undef,
        stdout      => undef,
        stderr      => undef,
        next_id     => 0,
        buffer      => '',
        stderr_tail => '',
        session     => undef,
        closed      => 0,
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

    my ($pid, $in_fh, $out_fh);

    my $ok = eval {
        $pid = IPC::Open3::open3( $in_fh, $out_fh, $err_fh, @$argv );
        1;
    };
    if (!$ok || !$pid) {
        my $why = $@ || 'open3 returned no pid';
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

# Read one response, skipping notifications and replies to other ids. Blocks
# until the deadline, draining stderr as it goes.
sub _read_response {
    my ($self, $id) = @_;

    my $timeout  = $self->{config}->timeout;
    my $deadline = time + $timeout;

    my $select = IO::Select->new($self->{stdout}, $self->{stderr});

    while (1) {
        # Serve any complete line already buffered before blocking.
        while ($self->{buffer} =~ s/\A([^\n]*)\n//) {
            my $line = $1;
            $line =~ s/\r\z//;
            next if $line =~ /^\s*$/;

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
            Mem20::TransportError->throw(
                message => "timed out after ${timeout}s waiting for response to request #$id"
                    . ' (' . $self->_stderr_tail . ')'
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
                    Mem20::TransportError->throw(
                        message => 'mem20 server closed stdout ('
                            . $self->_stderr_tail . ')'
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

# Non-blocking drain used when composing an error message mid-call.
sub _drain_stderr {
    my ($self) = @_;
    return unless $self->{stderr};

    while (1) {
        my $chunk = '';
        my $n = sysread($self->{stderr}, $chunk, 4096);
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
            Mem20::TransportError->throw(
                message => 'mem20 server process has exited ('
                    . $self->_stderr_tail . ')'
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

=head1 METHODS

=over 4

=item C<< new(config => $cfg) >>

=item C<< request($method, \%params) >> - returns C<result>; throws on an error object.

=item C<< notify($method, \%params) >> - notification, no reply.

=item C<initialize_session> - idempotent MCP handshake.

=item C<close> - SIGTERM, grace period, SIGKILL, reap.

=item C<pid>, C<session>, C<config>

=back

=cut
