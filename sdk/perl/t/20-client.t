use strict;
use warnings;

use Test::More;
use Cwd qw(abs_path);
use File::Basename qw(dirname);

use Mem20::Config;
use Mem20::Client;
use Mem20::Errors;

# Everything here drives a REAL child process over REAL pipes (the script in
# t/support/), on purpose: a mocked transport passes even when the framing is
# wrong, which is the bug this file exists to catch.

my $HERE  = abs_path( dirname(__FILE__) );
my $FAKE  = abs_path("$HERE/support/fake_mcp_server.pl");

sub config_for {
    my ($mode) = @_;
    return Mem20::Config->new(
        server_command => [ $^X, $FAKE, $mode ],
        timeout        => 5,
    );
}

subtest 'tool() accepts a flat pair list and a hashref, and refuses a mix' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    # The README used to document tool($name, { ... }) and that form silently
    # marshalled {"HASH(0x...)": null} as the arguments.
    my $by_hashref = $client->tool( 'memory_recall', { query => 'sky', limit => 5 } );
    like( $client->text($by_hashref), qr/sky is blue/, 'hashref form works' );

    my $by_pairs = $client->tool( 'memory_recall', query => 'sky', limit => 5 );
    like( $client->text($by_pairs), qr/sky is blue/, 'flat pair form works' );

    my $sent = $client->text( $client->tool( 'memory_store',
        content => 'x', epistemic_status => 'observed' ) );
    my $decoded = decode_json_safe($sent);
    is( ref $decoded->{stored}, 'HASH', 'arguments reached the server as an object' );
    is( $decoded->{stored}{content}, 'x', 'content survived marshalling' );

    my $err = Mem20::Errors::caught(
        sub { $client->tool( 'memory_recall', { query => 'sky' }, 'limit', 5 ) }
    );
    ok( ref $err && $err->isa('Mem20::ValidationError'), 'mixing forms is refused' );

    my $odd = Mem20::Errors::caught( sub { $client->tool( 'memory_recall', 'query' ) } );
    ok( ref $odd && $odd->isa('Mem20::ValidationError'), 'an odd-length list is refused' );

    $client->close;
};

subtest 'text() works as a function and as a method' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );
    my $hits   = $client->memory_recall( query => 'sky' );

    # The README documented Mem20::Client::text($hits); that form used to
    # return '' because the envelope was consumed as the invocant.
    is( Mem20::Client::text($hits), "the sky is blue\nwater is wet", 'function form' );
    is( $client->text($hits),      "the sky is blue\nwater is wet", 'method form' );
    is( Mem20::Client::text(undef), '', 'undef is empty, not an error' );

    $client->close;
};

subtest 'the handshake happens lazily, without an explicit connect' => sub {
    # MCP requires initialize before any other request. connect() used to be the
    # only thing that sent it, so a caller that followed the README's "calls
    # connect on demand" promise got -32602 "Invalid request parameters" on its
    # first tool call.
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $result = eval { $client->memory_recall( query => 'sky', limit => 3 ) };
    ok( !$@, 'first call succeeded with no explicit connect()' )
        or diag("error: $@");

    ok( $client->transport->session, 'a session was established on demand' );
    is( $client->text($result), "the sky is blue\nwater is wet", 'and the call returned real data' );

    $client->close;
};

subtest 'tools/list, tool_names and schemas' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $names = $client->tool_names;
    ok( ref $names eq 'ARRAY' && @$names, 'tool_names returns names' );
    ok( ( grep { $_ eq 'memory_store' } @$names ), 'memory_store advertised' );

    my $schema = $client->tool_schema('memory_store');
    is_deeply( $schema->{required}, [ 'content', 'epistemic_status' ],
        'the advertised required list is what the client validates against' );

    ok( $client->tool_schema('nope_not_here') == undef, 'an unknown tool has no schema' );

    $client->close;
};

subtest 'memory_store requires content and epistemic_status locally' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $no_content = Mem20::Errors::caught(
        sub { $client->memory_store( epistemic_status => 'observed' ) }
    );
    ok( ref $no_content && $no_content->isa('Mem20::ValidationError'),
        'content is required' );

    my $no_status = Mem20::Errors::caught( sub { $client->memory_store( content => 'x' ) } );
    ok( ref $no_status && $no_status->isa('Mem20::ValidationError'),
        'epistemic_status is required' );
    like( $no_status->message, qr/epistemic_status is required/, 'message is explicit' );

    # invented content belongs in the simulated partition, and the live server
    # does NOT enforce that despite what its own tool description says.
    my $imagined = Mem20::Errors::caught(
        sub { $client->memory_store( content => 'x', epistemic_status => 'imagined' ) }
    );
    ok( ref $imagined && $imagined->isa('Mem20::ValidationError'),
        'imagined is refused on the grounded store' );
    like( $imagined->message, qr/memory_simulate_store/, 'and pointed at the right tool' );

    my $nonsense = Mem20::Errors::caught(
        sub { $client->memory_store( content => 'x', epistemic_status => 'wishful' ) }
    );
    ok( ref $nonsense && $nonsense->isa('Mem20::ValidationError'),
        'an unknown epistemic_status is refused' );

    $client->close;
};

subtest 'memory_store joins a tag array into the string the schema wants' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $stored = $client->text(
        $client->memory_store(
            content          => 'x',
            epistemic_status => 'observed',
            tags             => [ 'a', 'b' ],
        )
    );
    my $args = decode_json_safe($stored)->{stored};
    is( $args->{tags}, 'a,b', 'an array is joined' );

    my $scalar_tags = decode_json_safe(
        $client->text( $client->memory_store(
            content => 'x', epistemic_status => 'observed', tags => 'a,b' ) )
    )->{stored};
    is( $scalar_tags->{tags}, 'a,b', 'a scalar passes through' );

    $client->close;
};

subtest 'result.isError=true becomes a ToolError' => sub {
    my $client = Mem20::Client->new( config => config_for('iserror') );

    my $err = Mem20::Errors::caught( sub { $client->tool('memory_status') } );

    ok( ref $err && $err->isa('Mem20::ToolError'), 'ToolError raised' );
    ok( $err->is_error,   'flagged is_error' );
    ok( !$err->soft_error, 'not a soft error' );
    like( $err->message, qr/Unknown tool/, 'server text carried through' );

    $client->close;
};

subtest 'isError=false with an Error payload becomes a soft ToolError' => sub {
    # This is the shape mem20 uses for a rejected argument. The protocol says
    # success, so a caller checking only for exceptions believes the write
    # landed.
    my $client = Mem20::Client->new( config => config_for('softerror') );

    my $err = Mem20::Errors::caught( sub { $client->memory_status } );

    ok( ref $err && $err->isa('Mem20::ToolError'), 'ToolError raised from a protocol success' );
    ok( $err->soft_error, 'flagged soft_error' );
    ok( !$err->is_error,  'the envelope said isError=false' );

    $client->close;
};

subtest 'a JSON-RPC error object maps to ToolError with code and data' => sub {
    my $client = Mem20::Client->new( config => config_for('error') );

    my $err = Mem20::Errors::caught( sub { $client->tool('memory_status') } );

    ok( ref $err && $err->isa('Mem20::ToolError'), 'ToolError raised' );
    is( $err->code, -32602, 'code is -32602' );
    is( $err->data->{tool}, 'memory_status', 'data is preserved' );

    $client->close;
};

subtest 'a job envelope is decoded and polled to a terminal state' => sub {
    my $client = Mem20::Client->new( config => config_for('job') );

    my $result = $client->tool( 'cog_plan', goal => 'ship it' );
    my $job    = $client->job_from($result);

    ok( $job, 'envelope decoded' );
    is( $job->{job_id}, 'deadbeef01', 'job_id read' );

    my $final = $client->wait_for_job( 'deadbeef01', timeout => 5, interval => 0.01 );
    is( $final->{status}, 'ok', 'polled until the job left running' );
    is( $final->{result}, 'the plan', 'and the real result came back' );

    # call_tool_await does both halves in one call.
    my $awaited = $client->call_tool_await( 'cog_plan', goal => 'ship it' );
    is( ref $awaited, 'HASH', 'call_tool_await returns the terminal status' );

    $client->close;
};

subtest 'an ordinary answer is not mistaken for a job envelope' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $result = $client->tool('memory_status');
    ok( !defined $client->job_from($result), 'no job_id, so not a job' );

    $client->close;
};

subtest 'a timeout throws instead of hanging, and reports stderr' => sub {
    my $client = Mem20::Client->new(
        config => Mem20::Config->new(
            server_command => [ $^X, $FAKE, 'silent' ],
            timeout        => 2,
        )
    );

    my $started = Time::HiRes::time();
    my $err     = Mem20::Errors::caught( sub { $client->tool('memory_status') } );
    my $elapsed = Time::HiRes::time() - $started;

    # The old drain blocked on stderr here and the call never returned at all.
    ok( ref $err && $err->isa('Mem20::TransportError'), 'TransportError raised' );
    like( $err->message, qr/timed out/, 'message says timed out' );
    ok( $elapsed < 8, "returned in ${elapsed}s rather than hanging" );

    $client->close;
};

subtest 'a chatty server does not deadlock on stderr' => sub {
    # 200 KB of stderr, well past the 64 KiB pipe buffer. A client reading only
    # stdout parks here forever.
    my $client = Mem20::Client->new( config => config_for('noisy') );

    my $result = eval { $client->tool('memory_status') };
    ok( !$@, 'the call completed despite the stderr flood' ) or diag("error: $@");
    is( $client->text($result), 'ok', 'and returned the real answer' );

    $client->close;
};

subtest 'invalid JSON from the server is a TransportError with the payload' => sub {
    my $client = Mem20::Client->new( config => config_for('garbage') );

    my $err = Mem20::Errors::caught( sub { $client->tool('memory_status') } );
    ok( ref $err && $err->isa('Mem20::TransportError'), 'TransportError raised' );
    like( $err->message, qr/this is not json/, 'the offending text is quoted' );

    $client->close;
};

subtest 'a child that exits mid-request is reported, not waited on' => sub {
    my $client = Mem20::Client->new( config => config_for('crash') );

    my $err = Mem20::Errors::caught( sub { $client->tool('memory_status') } );
    ok( ref $err && ( $err->isa('Mem20::TransportError') || $err->isa('Mem20::ToolError') ),
        'a transport-level error is raised' );
    like( $err->message, qr/(closed|exited|failed|timed out)/i, 'and it says what happened' );

    $client->close;
};

subtest 'dynamic dispatch reaches advertised tools and rejects the rest' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    is( $client->text( $client->memory_status ), 'ok', 'advertised tool dispatch' );
    ok( $client->can('memory_status'), 'can() agrees' );
    ok( !$client->can('no_such_tool'), 'and is false for an unadvertised name' );

    my $err = Mem20::Errors::caught( sub { $client->no_such_tool } );
    ok( ref $err && $err->isa('Mem20::ConfigurationError'), 'unadvertised name fails loudly' );

    $client->close;
};

subtest 'close is idempotent and leaves no child running' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );
    $client->tool('memory_status');

    my $pid = $client->transport->pid;
    ok( $pid && $pid > 0, 'child is running' );

    $client->close;
    ok( !$client->transport->pid, 'pid cleared' );

    # waitpid(-1, WNOHANG) must find nothing left to reap: a leaked child
    # would still hold the store lock.
    my $left = waitpid( -1, 1 );
    is( $left, -1, 'no zombie left behind' );

    $client->close;
    pass('second close is a no-op');
};

subtest 'verify_surface reports the compiled expectation and the live count' => sub {
    my $client = Mem20::Client->new( config => config_for('ok') );

    my $surface = $client->verify_surface;
    is( $surface->{tools}, 5, 'counts what the server actually advertises' );
    is( $surface->{expected_tools}, 270, 'and reports the compiled expectation' );
    is( $surface->{domains}, 27, 'domains come from the compiled constant' );
    is( $surface->{ok}, 0, 'a 5-tool server does not satisfy a 270-tool contract' );

    $client->close;
};

sub decode_json_safe {
    my ($text) = @_;
    my $decoded = eval { JSON::PP->new->utf8->decode($text) };
    return ref $decoded eq 'HASH' ? $decoded : {};
}

done_testing();
