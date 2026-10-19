package Mem20::Client;
use strict;
use warnings;

use JSON::PP ();
use HTTP::Tiny ();

use Mem20::Config;
use Mem20::Errors;
use Mem20::Transport::Stdio;

# Threadless, but reentrant-safe: one client owns one transport, and the
# transport serialises calls, so a client can be shared across a whole program
# and handed between modules without coordinating.
#
# The surface mirrors the Ruby gem's Mem20::Client method for method:
#
#   tool, tools, tool_names
#   memory_store, memory_recall
#   health, ready, healthy, metrics
#   close / shutdown
#   dynamic dispatch: any tool the server registers can be called by name
#
# plus ->connect, because Perl has no lazy-attribute idiom as pleasant as
# Ruby's and an explicit handshake is easier to reason about than an implicit
# one. Calls still connect on demand, so connect() is an optimisation, not a
# requirement.

sub new {
    my ($class, %args) = @_;

    my $config = $args{config};
    if (!$config) {
        my %options = map { $_ => $args{$_} } grep { $_ ne 'config' } keys %args;
        $config = Mem20::Config->from_env(%options);
    }

    # Freeze: a running client's config must not change underneath it.
    $config->restrict if $config->can('restrict') && !$config->is_frozen;

    my $self = bless {
        config     => $config,
        transport  => undef,
        tool_names => undef,
        http       => HTTP::Tiny->new(timeout => int( $config->timeout || 30 )),
    }, $class;

    return $self;
}

sub config { $_[0]{config} }

# Start the child server and complete the MCP handshake. Idempotent.
sub connect {
    my ($self) = @_;
    $self->_transport->initialize_session;
    return $self;
}

sub _transport {
    my ($self) = @_;
    return $self->{transport} ||= Mem20::Transport::Stdio->new( config => $self->{config} );
}

sub transport { $_[0]->_transport }

# Call any mem20 tool by name.
sub tool {
    my ($self, $name, %params) = @_;
    Mem20::ConfigurationError->throw(message => 'tool name is required')
        unless defined $name && length $name;

    return $self->_transport->request(
        'tools/call',
        { name => "$name", arguments => _objectify(\%params) },
    );
}

# List the tools the server exposes.
sub tools {
    my ($self) = @_;
    return $self->_transport->request( q{tools/list}, {} );
}

# The names of every registered tool, cached after the first call.
sub tool_names {
    my ($self) = @_;
    return $self->{tool_names} if $self->{tool_names};

    my $listing = $self->tools;
    my @names = map { $_->{name} } grep { ref $_ eq 'HASH' } @{ $listing->{tools} || [] };
    $self->{tool_names} = \@names;
    return $self->{tool_names};
}

# ---------------------------------------------------------- memory primitives

# Store a fact. `tags` may be an arrayref (joined into the comma-separated form
# the server expects) or a pre-formatted string.
sub memory_store {
    my ($self, %args) = @_;

    Mem20::ConfigurationError->throw(message => 'content is required for memory_store')
        unless defined $args{content};

    my %payload = (
        content  => $args{content},
        category => defined $args{category} ? $args{category} : 'general',
    );

    if (defined $args{tags}) {
        $payload{tags} = ref $args{tags} eq 'ARRAY'
            ? join(',', @{ $args{tags} })
            : "$args{tags}";
    }

    return $self->tool( 'memory_store', %payload );
}

# Search stored facts.
sub memory_recall {
    my ($self, %args) = @_;

    Mem20::ConfigurationError->throw(message => 'query is required for memory_recall')
        unless defined $args{query};

    my %payload = ( query => $args{query} );
    $payload{category} = $args{category} if defined $args{category};
    $payload{limit}    = $args{limit}    if defined $args{limit};

    return $self->tool( 'memory_recall', %payload );
}

# The plain-text payload of a tool-result envelope.
#
# The server returns { content => [ { type => 'text', text => ... }, ... ] },
# but a tool may return a bare string or several parts, so all three shapes are
# accepted rather than making every caller guard.
sub text {
    my ($self, $result) = @_;

    return '' unless defined $result;
    return "$result" unless ref $result eq 'HASH';

    my $parts = $result->{content};
    return '' unless ref $parts eq 'ARRAY';

    my @texts;
    for my $part (@$parts) {
        next unless ref $part eq 'HASH';
        push @texts, $part->{text} if defined $part->{text};
    }
    return join "\n", @texts;
}

# --------------------------------------------------------------- health surface

# GET /health -> decoded JSON, or undef when the endpoint is not answering.
sub health {
    my ($self) = @_;
    my $body = eval { $self->_http_get('/health') };
    return $@ ? undef : $body;
}

# GET /ready -> decoded JSON, or undef when the endpoint is not answering.
sub ready {
    my ($self) = @_;
    my $body = eval { $self->_http_get('/ready') };
    return $@ ? undef : $body;
}

# True when GET :port/health answers with a 2xx status.
sub healthy {
    my ($self) = @_;
    my $url = $self->{config}->health_url . '/health';
    my $res = eval { $self->{http}->get($url) };
    return 0 if !$res;
    return $res->{success} ? 1 : 0;
}

# Decoded counters from GET :port/metrics.
sub metrics {
    my ($self) = @_;
    return $self->_http_get('/metrics');
}

sub close {
    my ($self) = @_;
    if ($self->{transport}) {
        $self->{transport}->close;
        $self->{transport} = undef;
    }
    $self->{tool_names} = undef;
    return;
}

sub shutdown { return $_[0]->close }

# ----------------------------------------------------------- dynamic dispatch

# Any tool the server registers can be called as a method:
#
#   $client->memory_status;
#   $client->cog_plan(goal => 'ship 3.0');
#
# Restricted to names the server actually advertises, so a typo fails loudly
# instead of silently doing nothing.
#
# AUTOLOAD is used rather than overriding can(): `can` is consulted by perl
# itself while resolving a method call, and a `can` that advertises a name
# without an AUTOLOAD to back it returns true and then dies "Can't locate
# object method". Advertising and dispatch have to come from the same place.
sub AUTOLOAD {
    my ($self, @args) = @_;

    my $name = our $AUTOLOAD;
    $name =~ s/.*:://;

    return if $name eq 'DESTROY';

    if ( !$self->_callable_tool($name) ) {
        Mem20::ConfigurationError->throw(
            message => "unknown mem20 tool '$name' (the server did not advertise it)"
        );
    }

    Mem20::ConfigurationError->throw(
        message => "$name takes named arguments only"
    ) if @args % 2;

    return $self->tool( $name, @args );
}

# True only for tools the server actually advertises.
sub _callable_tool {
    my ($self, $name) = @_;

    return 0 if !defined $name || !length $name;

    my $known = eval { $self->tool_names };
    return 0 if !$known;

    my %known = map { $_ => 1 } @$known;
    return $known{$name} ? 1 : 0;
}

# Complement of the AUTOLOAD above, so `$client->can('memory_status')` is true
# for advertised tools and false otherwise — checked against the server's own
# list rather than assumed.
sub can {
    my ( $self, $name ) = @_;

    my $installed = UNIVERSAL::can( __PACKAGE__, $name );
    return $installed if $installed;

    return undef if ref $self ne __PACKAGE__;
    return undef if !defined $name;

    # AUTOLOAD backs every advertised tool with the same sub.
    return undef if !$self->_callable_tool($name);
    return \&AUTOLOAD;
}

# ---------------------------------------------------------------- internals

sub _http_get {
    my ($self, $path) = @_;

    my $url = $self->{config}->health_url . $path;
    my $res = $self->{http}->get($url);

    if (!$res->{success}) {
        my $why = $res->{status} ? "HTTP $res->{status}" : ( $res->{content} || 'no response' );
        Mem20::TransportError->throw(message => "could not read $url: $why");
    }

    my $decoded = eval { JSON::PP->new->utf8->decode( $res->{content} ) };
    if ($@) {
        my $why = $@;
        chomp $why;
        Mem20::TransportError->throw(message => "could not decode $url: $why");
    }
    return $decoded;
}

# Keep tool arguments a JSON object, never an array.
sub _objectify {
    my ($hash) = @_;
    return {} if !%$hash;
    return { %$hash };
}

1;
__END__

=head1 NAME

Mem20::Client - facade over the mem20 tool surface

=head1 SYNOPSIS

    use Mem20;
    use Mem20::Client;

    my $client = Mem20::Client->new;
    $client->connect;

    $client->memory_store(content => 'the sky is blue', category => 'general');
    my $out = $client->memory_recall(query => 'sky', limit => 5);
    print Mem20::Client::text($out);

    $client->memory_status;                  # any registered tool
    $client->close;

=head1 DESCRIPTION

C<tool> reaches every tool the server registers. The named accessors cover the
memory primitives; dynamic dispatch covers everything else, so new server tools
do not need SDK changes.

=head1 METHODS

=over 4

=item C<< new(%options) >> - takes C<config =E<gt> $cfg> or the same options C<Mem20::Config> accepts.

=item C<connect> - start the child server and complete the MCP handshake. Idempotent.

=item C<< tool($name, %params) >> - call any tool.

=item C<tools>, C<tool_names> - the server's advertisement (names cached).

=item C<< memory_store(%args) >>, C<< memory_recall(%args) >> - the memory primitives.

=item C<< text($result) >> - flatten a tool-result envelope to plain text.

=item C<health>, C<ready>, C<healthy>, C<metrics> - the HTTP health surface.

=item C<close> / C<shutdown> - stop the child and release the transport.

=back

=head1 DYNAMIC DISPATCH

Any advertised tool is callable by name and returns a coderef from C<can>, so
C<< $client->can('memory_status') >> is true only when the server really
offers it.

=cut
