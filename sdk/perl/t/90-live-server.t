use strict;
use warnings;

use Test::More;
use Mem20::Config;
use Mem20::Client;
use Mem20::Errors;
use Mem20::Version ();

# Live verification against a REAL mem20 server.
#
# Gated on purpose: this file SKIPS unless MEM20_MCP_DIR (a mem20 checkout) and
# MEM20_PYTHON (an interpreter with mem20's dependencies installed) are set, so
# `prove -Ilib t/*.t` stays green on a machine that has no server. Run it with
#
#   MEM20_MCP_DIR=/opt/mem20/mcp MEM20_PYTHON=python3 prove -Ilib t/90-live-server.t
#
# Everything asserted here was established by probing the server, not by
# reading its docs: see sdk/perl/AUDIT.md for the transcripts.

my $MCP_DIR = $ENV{MEM20_MCP_DIR};
my $PYTHON  = $ENV{MEM20_PYTHON};

plan skip_all => 'set MEM20_MCP_DIR and MEM20_PYTHON to run the live-server tests'
    unless $MCP_DIR && $PYTHON && -d $MCP_DIR;

plan skip_all => "MEM20_MCP_DIR ($MCP_DIR) does not contain mcp_server.py"
    unless -f "$MCP_DIR/mcp_server.py";

# A private store so the test never writes into a real deployment's memory.
my $STORE = "/tmp/mem20-perl-live-$$.json";

my $client = Mem20::Client->new(
    config => Mem20::Config->new(
        server_command => [ $PYTHON, 'mcp_server.py' ],
        cwd            => $MCP_DIR,
        timeout        => 60,
        env            => { MEM20_DB_PATH => $STORE },
    )
);

END {
    eval { $client->close if $client };
    unlink $STORE if $STORE && -e $STORE;
}

subtest 'handshake' => sub {
    # This also proves Config->cwd is applied: mcp_server.py is a relative path
    # and this test file lives in sdk/perl/t/, so without the chdir the child
    # would fail with "can't open file '<sdk/perl>/mcp_server.py'".
    $client->connect;
    my $session = $client->transport->session;

    ok( $session, 'session established' );
    is( $session->{protocol_version}, $Mem20::Version::PROTOCOL_VERSION,
        'protocol revision matches the SDK constant' );
    is( $session->{server_info}{name}, 'mem20-mcp', 'server identifies as mem20-mcp' );

    # serverInfo.version is an empty string in mem20 3.0.0. Asserting on it
    # would be asserting on a bug, so only the name is checked.
    is( $session->{server_info}{version}, '', 'serverInfo.version is empty (known upstream)' );
};

subtest 'the live surface matches what this SDK was compiled against' => sub {
    my $surface = $client->verify_surface;

    is( $surface->{tools}, $Mem20::Version::SURFACE_TOOL_COUNT,
        "tools/list returns $Mem20::Version::SURFACE_TOOL_COUNT tools" );
    is( $surface->{expected_tools}, 270, 'SDK constant is 270' );
    is( $surface->{domains}, 27, 'SDK constant says 27 domain modules' );
    is( $surface->{ok}, 1, 'surface check passes' );

    my $names = $client->tool_names;
    is( scalar @$names, scalar( keys %{ { map { $_ => 1 } @$names } } ),
        'every advertised tool name is unique' );

    # Spot-check that the domain families are actually present, so the count
    # cannot be satisfied by 270 copies of nothing.
    ok( $client->can('memory_store'),      'memory domain bound' );
    ok( $client->can('cog_plan'),          'cognitive domain bound' );
    ok( $client->can('job_status'),        'inline job domain bound' );
    ok( $client->can('memory_simulate_store'), 'simulated partition bound' );
};

subtest 'end-to-end round trip through the grounded partition' => sub {
    my $marker = 'sdk-live-marker-' . int( rand(1_000_000) );

    my $stored = $client->memory_store(
        content          => "perl sdk live round trip $marker",
        category         => 'project',
        tags             => [ 'sdk', 'live' ],
        epistemic_status => 'observed',
    );
    like( $client->text($stored), qr/Record ID:/, 'store returned a record id' );

    my $recalled = $client->memory_recall( query => $marker, limit => 5 );
    like( $client->text($recalled), qr/\Q$marker\E/, 'the marker comes back from recall' );
};

subtest 'missing epistemic_status is refused before it reaches the server' => sub {
    # The live server answers this with isError=false and stores an empty fact,
    # so a client that forwarded it would report a successful write that lost
    # its content.
    my $err = Mem20::Errors::caught( sub { $client->memory_store( content => 'x' ) } );

    ok( ref $err && $err->isa('Mem20::ValidationError'), 'refused locally' );
    like( $err->message, qr/epistemic_status is required/, 'message names the argument' );
};

subtest 'an unknown tool raises instead of looking like success' => sub {
    # The server answers with a protocol SUCCESS carrying result.isError.
    my $err = Mem20::Errors::caught( sub { $client->tool('no_such_tool_xyz', {}) } );

    ok( ref $err && $err->isa('Mem20::ToolError'), 'ToolError raised' );
    like( $err->message, qr/Unknown tool/i, 'server text carried through' );
    ok( $err->is_error, 'flagged as a hard error' );
};

subtest 'a rejected epistemic_status raises as a soft error' => sub {
    # isError=false, text starts "Error". Treating this as success is how a
    # dropped write becomes a believed fact.
    my $err = Mem20::Errors::caught(
        sub { $client->tool( 'memory_store', content => 'x', epistemic_status => 'not_a_status' ) }
    );

    ok( ref $err && $err->isa('Mem20::ToolError'), 'ToolError raised' );
    ok( $err->soft_error, 'flagged soft_error' );
    ok( !$err->is_error,  'envelope said isError=false' );
};

subtest 'a long-running tool returns a pollable job that resolves' => sub {
    my $result = $client->tool( 'cog_plan', goal => 'verify the perl sdk binding' );
    my $job    = $client->job_from($result);

    ok( $job, 'job envelope decoded' );
    ok( $job->{job_id}, 'job_id present' );

    my $final = $client->wait_for_job( $job->{job_id}, timeout => 60, interval => 0.2 );
    ok( defined $final->{status}, 'polling produced a status' );
    note( "final job status: " . ( $final->{status} // '?' ) );
};

# The transport accessor builds one on demand, so capture the live object
# before closing rather than asking for it afterwards.
my $transport = $client->transport;
$client->close;
ok( !$transport->pid, 'child reaped on close' );

done_testing();
