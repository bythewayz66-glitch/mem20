use strict;
use warnings;

use Test::More;
use Cwd qw(abs_path);

use Mem20::Config;
use Mem20::Client;
use Mem20::Errors;

# These tests drive a REAL child process over REAL pipes (t/support/
# fake_mcp_server.pl). Nothing is mocked, so a framing bug, a buffering bug or
# a deadlock shows up here rather than in production.

my $SUPPORT = abs_path( __FILE__ );
$SUPPORT =~ s{/t/[^/]+$}{/t/support};
my $FAKE = "$SUPPORT/fake_mcp_server.pl";

sub config_for {
    my ($mode, %overrides) = @_;
    return Mem20::Config->new(
        server_command => [ $^X, $FAKE, $mode ],
        timeout        => 10,
        %overrides,
    );
}

subtest 'initialize handshake' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );
    $client->connect;

    my $session = $client->transport->session;
    ok( $session, 'session established' );
    is( $session->{protocol_version}, '2025-06-18', 'protocol revision negotiated' );
    is( $session->{server_info}{name}, 'fake-mem20', 'server info surfaced' );

    $client->close;
};

subtest 'connect is idempotent' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    $client->connect;
    my $first = $client->transport;
    $client->connect;
    my $second = $client->transport;

    is( $first, $second, 'second connect returns the same transport' );
    $client->close;
};

subtest 'tools/list and tool_names' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $listing = $client->tools;
    is( scalar @{ $listing->{tools} }, 4, 'four tools advertised' );

    my $names = $client->tool_names;
    is_deeply( $names, [qw(memory_store memory_recall memory_status cog_plan)], 'names extracted in order' );

    # Cached: a second call must not re-request.
    is( $client->tool_names, $names, 'tool_names memoised' );

    $client->close;
};

subtest 'memory_store sends the documented arguments' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $result = $client->memory_store( content => 'prod runs build 4127', tags => [ 'prod', 'build' ] );
    my $text   = $client->text($result);

    like( $text, qr/"content":"prod runs build 4127"/, 'content reached the server' );
    like( $text, qr/"category":"general"/,             'default category applied' );
    like( $text, qr/"tags":"prod,build"/,              'array tags joined with commas' );

    my $stringy = $client->memory_store( content => 'x', category => 'ops', tags => 'a,b' );
    like( $client->text($stringy), qr/"tags":"a,b"/, 'pre-formatted string tags passed through' );

    $client->close;
};

subtest 'memory_store requires content' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $err = Mem20::Errors::caught( sub { $client->memory_store( category => 'general' ) } );
    ok( ref $err && $err->isa('Mem20::ConfigurationError'), 'missing content throws' );

    $client->close;
};

subtest 'memory_recall returns every text part' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $result = $client->memory_recall( query => 'sky', limit => 5 );
    my $text   = $client->text($result);

    is( $text, "the sky is blue\nwater is wet", 'parts joined with newlines' );

    $client->close;
};

subtest 'memory_recall requires query' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $err = Mem20::Errors::caught( sub { $client->memory_recall( limit => 5 ) } );
    ok( ref $err && $err->isa('Mem20::ConfigurationError'), 'missing query throws' );

    $client->close;
};

subtest 'a JSON-RPC error object becomes a ToolError' => sub {
    my $client = Mem20::Client->new( config => config_for('error') );

    my $err = Mem20::Errors::caught( sub { $client->memory_recall( query => 'x' ) } );

    ok( ref $err && $err->isa('Mem20::ToolError'), 'ToolError raised' );
    like( $err->message, qr/invalid params/, 'server message carried through' );
    is( $err->code, -32602, 'numeric code preserved' );
    is_deeply( $err->data, { tool => 'memory_recall' }, 'structured data preserved' );

    $client->close;
};

subtest 'a crashing server is a TransportError, not a hang' => sub {
    my $client = Mem20::Client->new( config => config_for('crash') );

    my $err = Mem20::Errors::caught( sub { $client->memory_recall( query => 'x' ) } );
    ok( ref $err && $err->isa('Mem20::TransportError'), 'TransportError raised' );
    like( $err->message, qr/closed stdout|exited/, 'message explains the child died' );

    $client->close;
};

subtest 'non-JSON output is reported, not silently ignored' => sub {
    my $client = Mem20::Client->new( config => config_for('garbage') );

    # No explicit connect(): in this mode the server answers EVERY request with
    # garbage, including initialize, so the lazy connect inside the tool call is
    # exactly what must be seen to fail cleanly.
    my $err = Mem20::Errors::caught( sub { $client->memory_recall( query => 'x' ) } );

    ok( ref $err && $err->isa('Mem20::TransportError'), 'TransportError raised' );
    like( $err->message, qr/invalid JSON/, 'message names the problem' );
    like( $err->message, qr/this is not json/, 'message includes the offending line' );

    $client->close;
};

subtest 'a chatty stderr does not deadlock the client' => sub {
    # The regression this guards: reading only stdout blocks forever once the
    # child fills its 64KiB stderr pipe buffer, because the child is then
    # blocked writing and never reaches its first reply.
    my $client = Mem20::Client->new( config => config_for('noisy') );

    my $err = Mem20::Errors::caught( sub { $client->memory_recall( query => 'sky' ) } );

    ok( !$err, 'call completed without timing out' )
        or diag( 'error: ' . ( ref $err ? $err->message : $err ) );

    $client->close;
};

subtest 'timeout is honoured and reported' => sub {
    # A child that starts and never answers. `crash` mode plus a 1s budget gets
    # there without depending on an external signal or a long wall-clock wait.
    my $client = Mem20::Client->new(
        config => Mem20::Config->new(
            server_command => [ $^X, $FAKE, 'crash' ],
            timeout        => 1,
        )
    );

    my $started = time;
    my $err     = Mem20::Errors::caught( sub { $client->memory_recall( query => 'x' ) } );
    my $elapsed = time - $started;

    ok( ref $err && $err->isa('Mem20::TransportError'), 'TransportError raised' );
    like( $err->message, qr/closed stdout|exited|timed out/, 'message explains the failure' );
    cmp_ok( $elapsed, '<', 30, "gave up promptly (${elapsed}s)" );

    $client->close;
};

subtest 'dynamic dispatch reaches any advertised tool' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    ok( $client->can('memory_status'), 'advertised tool is callable' );
    ok( !$client->can('not_a_tool'),    'unadvertised name is not callable' );

    my $out = $client->memory_status;
    is( $client->text($out), 'ok', 'dynamic call returned the result' );

    $client->close;
};

subtest 'text() tolerates the shapes the server may return' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    is( $client->text( undef ), '', 'undef -> empty string' );
    is( $client->text('bare'),  'bare', 'bare string passed through' );
    is( $client->text( {} ),    '', 'no content key -> empty string' );
    is(
        $client->text( { content => [ { type => 'text', text => 'a' }, { type => 'image' }, { type => 'text', text => 'b' } ] } ),
        "a\nb",
        'only text parts are joined, non-text parts skipped'
    );

    $client->close;
};

subtest 'close is idempotent and releases the child' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );
    $client->connect;

    my $transport = $client->transport;
    ok( $transport->pid, 'child process running' );

    $client->close;
    ok( !$transport->pid, 'pid cleared after close' );

    $client->close;    # must not die
    pass('second close is a no-op');
};

subtest 'a client freezes its config' => sub {
    my $cfg    = Mem20::Config->new;
    my $client = Mem20::Client->new( config => $cfg );

    ok( $cfg->is_frozen, 'config frozen by the client' );

    my $err = Mem20::Errors::caught( sub { $cfg->health_port(1234) } );
    ok( ref $err && $err->isa('Mem20::ConfigurationError'), 'mutation refused while a client exists' );

    $client->close;
};

subtest 'health surface degrades to undef when nothing is listening' => sub {
    # Port 1 is reserved and nothing listens on it, so this exercises the
    # "endpoint not answering" path rather than the happy path.
    my $client = Mem20::Client->new(
        config => Mem20::Config->new( health_host => '127.0.0.1', health_port => 1, timeout => 1 )
    );

    is( $client->health,  undef, 'health returns undef, does not throw' );
    is( $client->ready,   undef, 'ready returns undef, does not throw' );
    is( $client->healthy, 0,     'healthy is false, does not throw' );

    my $err = Mem20::Errors::caught( sub { $client->metrics } );
    ok( ref $err && $err->isa('Mem20::TransportError'), 'metrics throws because it has no undef contract' );
};

done_testing();
