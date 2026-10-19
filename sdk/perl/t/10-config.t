use strict;
use warnings;

use Test::More;

use Mem20::Config;
use Mem20::Errors;
use Mem20::Version ();

# Config is where most of the SDK's error handling lives: it is the one place
# that validates user input, so every rule gets a test.

subtest 'defaults' => sub {
    my $cfg = Mem20::Config->new;

    is_deeply( $cfg->server_command, [ 'python3', 'mcp/mcp_server.py' ], 'default server_command' );
    is( $cfg->cwd,              undef,           'no default cwd' );
    is( $cfg->health_port,      8080,            'default health_port' );
    is( $cfg->health_host,      '127.0.0.1',     'default health_host' );
    is( $cfg->timeout,          30.0,            'default timeout' );
    is( $cfg->protocol_version, $Mem20::Version::PROTOCOL_VERSION, 'protocol_version from Version' );
    is_deeply( $cfg->env, {}, 'empty default env' );
};

subtest 'options override defaults' => sub {
    my $cfg = Mem20::Config->new( health_port => 9090, timeout => 5 );

    is( $cfg->health_port, 9090, 'health_port overridden' );
    is( $cfg->timeout,     5,    'timeout overridden' );
};

subtest 'unknown options are rejected by name' => sub {
    my $err = Mem20::Errors::caught( sub { Mem20::Config->new( nope => 1, also_nope => 2 ) } );

    ok( ref $err && $err->isa('Mem20::ConfigurationError'), 'throws ConfigurationError' );
    like( $err->message, qr/unknown configuration option/, 'message explains the problem' );
    like( $err->message, qr/also_nope/, 'names the offending key' );
    like( $err->message, qr/nope/,      'names every offending key' );
};

subtest 'validation' => sub {
    my @cases = (
        [ { server_command => [] },        qr/server_command/, 'empty server_command' ],
        [ { timeout        => 0 },         qr/timeout/,        'zero timeout' ],
        [ { timeout        => -1 },        qr/timeout/,        'negative timeout' ],
        [ { health_port    => 0 },         qr/health_port/,    'port 0' ],
        [ { health_port    => 70_000 },    qr/health_port/,    'port above 65535' ],
        [ { health_port    => 'abc' },     qr/health_port/,    'non-numeric port' ],
        [ { protocol_version => '' },      qr/protocol_version/, 'empty protocol_version' ],
        [ { health_host    => '' },        qr/health_host/,    'empty health_host' ],
        [ { env            => [] },        qr/env/,            'env not a hashref' ],
    );

    for my $case (@cases) {
        my ($options, $pattern, $label) = @$case;
        my $err = Mem20::Errors::caught( sub { Mem20::Config->new(%$options) } );
        ok( ref $err && $err->isa('Mem20::ConfigurationError'), "$label throws" )
            or diag("got: " . (ref $err ? $err->message : $err));
        like( $err->message, $pattern, "$label message names the field" ) if ref $err;
    }
};

subtest 'environment mapping' => sub {
    my $cfg = Mem20::Config->from_options_and_env(
        {},
        {
            MEM20_STORE_PATH   => '/tmp/store',
            MEM20_COG_PATH     => '/tmp/cog',
            MEM20_LLM_MODEL    => 'llama',
            MEM20_LLM_BASE_URL => 'http://localhost:8000',
            MEM20_HEALTH_PORT  => '9091',
        }
    );

    is( $cfg->store_path,   '/tmp/store',          'MEM20_STORE_PATH' );
    is( $cfg->cog_path,     '/tmp/cog',            'MEM20_COG_PATH' );
    is( $cfg->llm_model,    'llama',               'MEM20_LLM_MODEL' );
    is( $cfg->llm_base_url, 'http://localhost:8000', 'MEM20_LLM_BASE_URL' );
    is( $cfg->health_port,  9091,                  'MEM20_HEALTH_PORT coerced to a number' );
};

subtest 'explicit options beat the environment' => sub {
    my $cfg = Mem20::Config->from_options_and_env(
        { store_path => '/explicit' },
        { MEM20_STORE_PATH => '/from-env' }
    );

    is( $cfg->store_path, '/explicit', 'option wins over env' );
};

subtest 'api key precedence' => sub {
    my $first = Mem20::Config->from_options_and_env( {}, { MEM20_LLM_API_KEY => 'a', NVAPI_KEY => 'b' } );
    is( $first->llm_api_key, 'a', 'MEM20_LLM_API_KEY wins' );

    my $second = Mem20::Config->from_options_and_env( {}, { NVAPI_KEY => 'b', NVIDIA_API_KEY => 'c' } );
    is( $second->llm_api_key, 'b', 'NVAPI_KEY beats NVIDIA_API_KEY' );

    my $third = Mem20::Config->from_options_and_env( {}, { NVIDIA_API_KEY => 'c' } );
    is( $third->llm_api_key, 'c', 'NVIDIA_API_KEY as last resort' );
};

subtest 'child_env carries the MEM20_* overrides only' => sub {
    my $cfg = Mem20::Config->new(
        store_path   => '/tmp/store',
        health_port  => 9092,
        env          => { HOME => '/root' },
    );

    my $env = $cfg->child_env;

    is( $env->{MEM20_STORE_PATH},  '/tmp/store', 'store path exported' );
    is( $env->{MEM20_HEALTH_PORT}, '9092',       'health port exported as a string' );
    is( $env->{HOME},              '/root',      'base env preserved' );
    ok( !exists $env->{MEM20_COG_PATH}, 'unset values are not exported as undef' );
};

subtest 'health_url' => sub {
    my $cfg = Mem20::Config->new( health_host => 'mem20.internal', health_port => 8443 );
    is( $cfg->health_url, 'http://mem20.internal:8443', 'assembled from host and port' );
};

subtest 'build applies the block then freezes' => sub {
    my $cfg = Mem20::Config->build( sub { $_[0]->health_port(7000) }, timeout => 9 );

    is( $cfg->health_port, 7000, 'block change applied' );
    is( $cfg->timeout,     9,    'option applied' );
    ok( $cfg->is_frozen, 'config frozen after build' );
};

subtest 'a frozen config refuses mutation' => sub {
    my $cfg = Mem20::Config->new->restrict;

    my $err = Mem20::Errors::caught( sub { $cfg->health_port(1234) } );
    ok( ref $err && $err->isa('Mem20::ConfigurationError'), 'setter throws on a frozen config' );
    like( $err->message, qr/frozen/, 'message says it is frozen' );
    is( $cfg->health_port, 8080, 'value unchanged' );
};

subtest 'setters re-validate' => sub {
    my $cfg = Mem20::Config->new;

    my $err = Mem20::Errors::caught( sub { $cfg->health_port(99_999) } );
    ok( ref $err && $err->isa('Mem20::ConfigurationError'), 'invalid value rejected at set time' );
    is( $cfg->health_port, 8080, 'previous good value retained' );

    $cfg->health_port(9000);
    is( $cfg->health_port, 9000, 'valid value accepted' );
};

subtest 'to_hash round-trips every known key' => sub {
    my $cfg  = Mem20::Config->new( health_port => 8123 );
    my %hash = $cfg->to_hash;

    for my $key ( Mem20::Config::KNOWN_KEYS() ) {
        ok( exists $hash{$key}, "to_hash has $key" );
    }
    is( $hash{health_port}, 8123, 'value survives the round trip' );
};

done_testing();
