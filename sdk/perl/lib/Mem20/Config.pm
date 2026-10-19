package Mem20::Config;
use strict;
use warnings;

use Mem20::Errors;
use Mem20::Version ();

# Configuration for a Mem20::Client.
#
# Same shape and the same validation rules as the Ruby gem's Mem20::Config, so
# one .env drives both SDKs identically:
#
#   MEM20_STORE_PATH   -> store_path
#   MEM20_COG_PATH     -> cog_path
#   MEM20_LLM_BASE_URL -> llm_base_url
#   MEM20_LLM_MODEL    -> llm_model
#   MEM20_LLM_API_KEY  -> llm_api_key  (NVAPI_KEY / NVIDIA_API_KEY also accepted)
#   MEM20_HEALTH_PORT  -> health_port
#
# A config is mutable while you are setting it up and is frozen by the client
# that adopts it (see restrict() ), so a running client's config cannot change
# underneath it.

my @KNOWN = qw(
    server_command cwd store_path cog_path
    llm_base_url llm_model llm_api_key
    health_port health_host protocol_version timeout env
);

my @ENV_MAP = (
    [ store_path   => 'MEM20_STORE_PATH' ],
    [ cog_path     => 'MEM20_COG_PATH' ],
    [ llm_base_url => 'MEM20_LLM_BASE_URL' ],
    [ llm_model    => 'MEM20_LLM_MODEL' ],
    # health_port belongs here as much as the others: it is read from
    # MEM20_HEALTH_PORT below, and the README documents the mapping. Leaving it
    # out of this table meant the child process never received the port it was
    # configured with, so the SDK probed one port while the server served
    # another.
    [ health_port  => 'MEM20_HEALTH_PORT' ],
);

my @API_KEY_VARS = qw(MEM20_LLM_API_KEY NVAPI_KEY NVIDIA_API_KEY);

sub KNOWN_KEYS  { return @KNOWN }
sub API_KEY_VARS { return @API_KEY_VARS }

# Attribute name => environment variable, as a flat hash (used by child_env).
sub ENV_MAP_HASH { return { map { $_->[0] => $_->[1] } @ENV_MAP } }

sub new {
    my ($class, %options) = @_;

    my %unknown = map { $_ => 1 } grep { !exists $class->defaults->{$_} } keys %options;
    if (keys %unknown) {
        Mem20::ConfigurationError->throw(
            message => 'unknown configuration option(s): ' . join(', ', sort keys %unknown)
        );
    }

    my %values = ( %{ $class->defaults }, %options );
    my $self = bless { values => $class->_normalize(%values) }, $class;
    return $self;
}

# The defaults. server_command is the argv the child server is exec'd with,
# relative to `cwd` when one is set.
sub defaults {
    return {
        server_command   => [ 'python3', 'mcp/mcp_server.py' ],
        cwd              => undef,
        store_path       => undef,
        cog_path         => undef,
        llm_base_url     => 'https://integrate.api.nvidia.com/v1',
        llm_model        => undef,
        llm_api_key      => undef,
        health_port      => 8080,
        health_host      => '127.0.0.1',
        protocol_version => $Mem20::Version::PROTOCOL_VERSION,
        timeout          => 30.0,
        env              => {},
    };
}

# Build a config, hand it to a block for setup, then freeze it.
#
#   my $cfg = Mem20::Config->build(sub { $_[0]->cwd('/opt/mem20') });
sub build {
    my ($class, $block, %options) = @_;
    my $cfg = $class->new(%options);
    $block->($cfg) if $block;
    return $cfg->restrict;
}

# Build a config, filling missing values from the process environment.
sub from_env {
    my ($class, %options) = @_;
    return $class->from_options_and_env(\%options, \%ENV);
}

# The testable form of from_env: the environment hash is passed in explicitly,
# so tests never depend on (or mutate) the real %ENV.
sub from_options_and_env {
    my ($class, $options, $env) = @_;
    my %from_env = $class->env_values($env);
    return $class->new(%from_env, %{ $options || {} });
}

# The documented MEM20_* values present in $env, as config attributes.
sub env_values {
    my ($class, $env) = @_;
    my %values;

    for my $pair (@ENV_MAP) {
        my ($attribute, $variable) = @$pair;
        my $value = $env->{$variable};
        $values{$attribute} = $value if defined $value;
    }

    if (defined(my $port = $env->{MEM20_HEALTH_PORT})) {
        $values{health_port} = $port;
    }

    for my $variable (@API_KEY_VARS) {
        my $key = $env->{$variable};
        if (defined $key && length $key) {
            $values{llm_api_key} = $key;
            last;
        }
    }

    return %values;
}

# Freeze the config so nothing can mutate it under a running client. Enforced
# in the setters below: after restrict() the setters throw.
sub restrict {
    my ($self) = @_;
    $self->{frozen} = 1;
    return $self;
}

sub is_frozen { return $_[0]{frozen} ? 1 : 0 }

sub _assert_mutable {
    my ($self, $name) = @_;
    Mem20::ConfigurationError->throw(
        message => "cannot modify frozen Mem20::Config (tried to set $name)"
    ) if $self->{frozen};
    return 1;
}

# Generic accessor/mutator for every known attribute.
for my $name (@KNOWN) {
    no strict 'refs';
    *{$name} = sub {
        my $self = shift;
        if (@_) {
            $self->_assert_mutable($name);
            my %merged = ( %{ $self->{values} }, $name => $_[0] );
            $self->{values} = Mem20::Config->_normalize(%merged);
            return $self;
        }
        return $self->{values}{$name};
    };
}

# The current values as a plain hash.
sub to_hash { return %{ $_[0]{values} } }

# The environment the child server is launched with: the base env plus the
# MEM20_* values this config carries.
sub child_env {
    my ($self) = @_;
    my %env = %{ $self->{values}{env} || {} };
    my $map = $self->ENV_MAP_HASH;

    for my $attribute (sort keys %$map) {
        my $value = $self->{values}{$attribute};
        next unless defined $value;
        $env{ $map->{$attribute} } = "$value";
    }
    return \%env;
}

sub health_url {
    my ($self) = @_;
    return sprintf 'http://%s:%d', $self->health_host, $self->health_port;
}

# Coerce scalars and validate the whole configuration. Runs on construction and
# again after every setter, so an invalid value can never be parked in the
# object and discovered later at call time.
sub _normalize {
    my ($class, %values) = @_;

    Mem20::ConfigurationError->throw(
        message => 'server_command must not be empty'
    ) unless ref $values{server_command} eq 'ARRAY' && @{ $values{server_command} };

    Mem20::ConfigurationError->throw(
        message => 'timeout must be positive'
    ) unless defined $values{timeout} && $values{timeout} =~ /^[0-9.]+$/ && $values{timeout} > 0;

    Mem20::ConfigurationError->throw(
        message => 'health_port must be an integer'
    ) unless defined $values{health_port} && $values{health_port} =~ /^\d+$/;

    Mem20::ConfigurationError->throw(
        message => 'health_port out of range: ' . $values{health_port}
    ) unless $values{health_port} >= 1 && $values{health_port} <= 65_535;

    Mem20::ConfigurationError->throw(
        message => 'protocol_version must be a non-empty string'
    ) unless defined $values{protocol_version} && length $values{protocol_version};

    Mem20::ConfigurationError->throw(
        message => 'health_host must be a non-empty string'
    ) unless defined $values{health_host} && length $values{health_host};

    Mem20::ConfigurationError->throw(
        message => 'env must be a hash reference'
    ) unless ref $values{env} eq 'HASH';

    $values{timeout}      = 0 + $values{timeout};
    $values{health_port}  = 0 + $values{health_port};
    $values{server_command} = [ @{ $values{server_command} } ];

    return \%values;
}

1;
__END__

=head1 NAME

Mem20::Config - configuration object for Mem20::Client

=head1 SYNOPSIS

    use Mem20::Config;

    # defaults, then environment overrides
    my $cfg = Mem20::Config->from_env;

    # block-style setup
    my $cfg = Mem20::Config->build(sub {
        my $c = shift;
        $c->cwd('/opt/mem20');
        $c->health_port(9090);
    });

=head1 DESCRIPTION

C<server_command> is the argv used to exec the mem20 server, run with
C<cwd> as the working directory when set. The remaining keys map onto the
documented C<MEM20_*> environment variables, so one C<.env> configures both
the server and the SDK.

Every value is validated on construction I<and> after every setter, so an
invalid value is rejected at the point you set it rather than surfacing as a
confusing failure on a later call.

=head1 METHODS

=over 4

=item C<< Mem20::Config->new(%options) >> - validate and build.

=item C<< Mem20::Config->build($block, %options) >> - build, apply the block, freeze.

=item C<< Mem20::Config->from_env(%options) >> - fill missing values from C<%ENV>.

=item C<< Mem20::Config->from_options_and_env(\%opts, \%env) >> - testable form.

=item C<< Mem20::Config->env_values(\%env) >> - the C<MEM20_*> values present.

=item C<to_hash>, C<child_env>, C<health_url>, C<restrict>, C<is_frozen> -
introspection and lifecycle.

=back

=head1 VALIDATION

C<server_command> non-empty; C<timeout> positive numeric; C<health_port> an
integer in 1..65535; C<protocol_version> and C<health_host> non-empty; C<env>
a hashref; unknown option keys rejected by name.

=cut
