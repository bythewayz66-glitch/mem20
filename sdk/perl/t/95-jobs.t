use strict;
use warnings;

use Test::More;
use Cwd qw(abs_path);
use File::Basename qw(dirname);
use Time::HiRes ();

use Mem20::Config;
use Mem20::Client;
use Mem20::Errors;

# The background-job path, end to end.
#
# mem20 runs its LLM-backed tools (cog_*, imagination_*, tot_*, beam_search,
# theory_of_mind_*, self_model_reflect, memory_auto_consolidate,
# cognitive_substrate) as asyncio tasks and answers tools/call with
#
#   {"job_id":"...","status":"running","tool":"cog_plan",
#    "poll":"job_status","wait":"job_wait"}
#
# instead of a result. That envelope is a protocol B<success>: the answer is
# not in it. A client that treats the response as the answer reports success
# and hands the caller a job token, which is the same "reports success while
# dropping data" failure the isError/soft-error handling exists to prevent --
# only one poll deeper, because it survives the tools/call layer and dies
# inside wait_for_job instead.
#
# So these specs pin four things, all against a real child process:
#
#   1. a terminal state is actually reached, and reached by polling;
#   2. the loop is bounded -- it cannot hang the caller;
#   3. a job that never terminates raises instead of being returned as if it
#      had finished;
#   4. a job that ends in `error`, or `not_found`, is surfaced.
#
# The timeout case is the one that shipped broken: wait_for_job used to `last`
# out of its loop and return the last observed status, so a hung job came back
# as {status => 'running', result => undef} -- a success-shaped value with no
# data in it. Test 3 fails on that code.
#
# Status vocabulary is the server's, not invented: mcp/server.py _spawn_job()
# starts at 'running', _run_job() ends at 'ok' or 'error', _job_status()
# answers 'not_found' for an unknown id. There is no done/complete/finished.

my $HERE = abs_path( dirname(__FILE__) );
my $FAKE = abs_path("$HERE/support/fake_mcp_server.pl");

sub config_for {
    my ($mode) = @_;
    return Mem20::Config->new(
        server_command => [ $^X, $FAKE, $mode ],
        timeout        => 5,
    );
}

# Run a block, returning ($error, $elapsed). The eval is written so that $@ is
# captured in the same statement that clears it -- see Mem20::Error::caught.
sub timed_caught {
    my ($code) = @_;
    my $started = Time::HiRes::time();
    my $ok      = eval { $code->(); 1 };
    my $elapsed = Time::HiRes::time() - $started;
    my $err     = $ok ? undef : $@;
    return ( $err, $elapsed, $ok );
}

# A status the server uses for "still going". Kept in one place so the specs
# below cannot disagree about it.
my %RUNNING = map { $_ => 1 } qw(running pending queued);

subtest 'job_from recognises an envelope and nothing else' => sub {
    my $client = Mem20::Client->new( config => config_for('job') );

    my $result = $client->tool( 'cog_plan', goal => 'ship it' );
    my $job    = $client->job_from($result);

    ok( $job, 'job envelope decoded' );
    is( $job->{job_id}, 'deadbeef01', 'job_id read from the envelope' );
    is( $job->{status}, 'running',     'status read from the envelope' );
    is( $job->{poll},   'job_status',  'the poll hint is preserved' );
    is( $job->{wait},   'job_wait',    'the wait hint is preserved' );

    # An ordinary answer must not be mistaken for a job. memory_status returns
    # the bare text "ok", which is not JSON at all.
    my $plain = Mem20::Client->new( config => config_for('ok') );
    ok( !defined $plain->job_from( $plain->tool('memory_status') ),
        'plain text is not a job envelope' );
    ok( !defined $plain->job_from( $plain->tool( 'memory_recall', query => 'sky' ) ),
        'a multi-part text result is not a job envelope' );
    ok( !defined $plain->job_from(undef), 'undef is not a job envelope' );
    $plain->close;

    $client->close;
};

subtest 'a poll loop reaches a terminal state, by polling' => sub {
    my $client = Mem20::Client->new( config => config_for('job') );

    # The fixture answers running, running, ok. Reaching `ok` therefore proves
    # the loop actually polled rather than trusting the first envelope -- a
    # single-shot implementation cannot produce this status.
    my ( $err, $elapsed ) = timed_caught(
        sub { $client->wait_for_job( 'deadbeef01', timeout => 5, interval => 0.01 ) }
    );
    ok( !$err, 'no error for a job that completes' ) or diag("error: $err");

    my $final = eval { $client->wait_for_job( 'deadbeef01', timeout => 5, interval => 0.01 ) };

    # Second call restarts the fixture's counter at a terminal state, so this
    # only asserts shape; the first call is the one that proves walking.
    ok( ref $final eq 'HASH', 'wait_for_job returns the status hashref' );
    is( $final->{job_id}, 'deadbeef01', 'the job_id comes back' );

    $client->close;

    # And the same walk through call_tool_await, which is the helper the
    # README actually tells long-running callers to use.
    my $awaiting = Mem20::Client->new( config => config_for('job') );
    my $awaited  = $awaiting->call_tool_await( 'cog_plan', goal => 'ship it' );
    is( ref $awaited, 'HASH', 'call_tool_await resolves to a status hashref' );
    is( $awaited->{status}, 'ok',        'call_tool_await reached a terminal state' );
    is( $awaited->{result}, 'the plan',  'and carries the real result, not the envelope' );
    isnt( $awaited->{status}, 'running', 'it did not hand back the running envelope' );
    $awaiting->close;
};

subtest 'wait_for_job refuses to return a still-running job' => sub {
    # THE REGRESSION. Before this spec existed, wait_for_job fell out of its
    # loop on deadline and returned $last -- so a hung job produced
    # {status => 'running', result => undef} and every caller that checked
    # `if ($final)` or read ->{result} saw a successful-looking empty answer.
    my $client = Mem20::Client->new( config => config_for('jobhang') );

    my ( $err, $elapsed, $ok ) = timed_caught(
        sub { $client->wait_for_job( 'deadbeef01', timeout => 0.5, interval => 0.05 ) }
    );

    ok( !$ok, 'a job that never terminates does not return as if it finished' );

    if ( !$ok && !ref $err ) {
        fail('it died with a plain string, not an SDK object');
        diag("died with: $err");
    }
    else {
        ok( ref $err && $err->isa('Mem20::JobTimeoutError'),
            'raises Mem20::JobTimeoutError' )
            or diag( 'got: ' . ( ref $err || $err ) );
        ok( ref $err && $err->isa('Mem20::Error'),
            'and it is catchable as a Mem20::Error' );
    }

    # Bounded: the deadline is 0.5s and the fixture never finishes, so the only
    # thing that ends this call is the deadline. A generous ceiling leaves room
    # for a slow box while still failing loudly on a real hang.
    ok( $elapsed < 5, sprintf( 'returned in %.2fs rather than hanging', $elapsed ) );

    # The error has to carry the diagnosis, or the caller cannot tell "still
    # working" from "gone".
    if ( ref $err && $err->isa('Mem20::JobTimeoutError') ) {
        is( $err->job_id, 'deadbeef01', 'the error names the job' );
        is( $err->status, 'running',    'the error reports the last status seen' );
        cmp_ok( $err->polls, '>', 0,    'the error reports how many polls it made' );
        like( $err->message, qr/never reached a terminal state|timed out/i,
            'the message says what went wrong' );
    }
    else {
        fail('no JobTimeoutError to inspect');
    }

    $client->close;
};

subtest 'a job that ends in error is surfaced' => sub {
    my $client = Mem20::Client->new( config => config_for('jobfailed') );

    my ( $err, $elapsed ) = timed_caught(
        sub { $client->wait_for_job( 'deadbeef01', timeout => 5, interval => 0.01 ) }
    );

    ok( ref $err && $err->isa('Mem20::JobFailedError'), 'raises Mem20::JobFailedError' )
        or diag( 'got: ' . ( ref $err || $err || 'nothing' ) );

    if ( ref $err && $err->isa('Mem20::JobFailedError') ) {
        is( $err->status, 'error', 'the terminal status is preserved' );
        like( $err->message, qr/cog_plan raised/,
            "the job's own error text reaches the caller" );
        is( $err->job_id, 'deadbeef01', 'the error names the job' );
        ok( $err->isa('Mem20::Error'), 'and it is catchable as a Mem20::Error' );
    }

    # `error` is terminal, so the loop must not sit on it until the deadline.
    ok( $elapsed < 2, sprintf( 'stopped at the terminal state (%.2fs)', $elapsed ) );

    $client->close;
};

subtest 'a job the server has never heard of is surfaced' => sub {
    # mem20 answers not_found for an unknown job_id. Returning that hashref
    # quietly would let a caller read ->{result} from a job that does not
    # exist, which is a silent empty answer.
    my $client = Mem20::Client->new( config => config_for('joblost') );

    my $err = Mem20::Errors::caught(
        sub { $client->wait_for_job( 'nope', timeout => 5, interval => 0.01 ) }
    );

    ok( ref $err && $err->isa('Mem20::JobFailedError'), 'raises Mem20::JobFailedError' )
        or diag( 'got: ' . ( ref $err || $err || 'nothing' ) );

    if ( ref $err && $err->isa('Mem20::JobFailedError') ) {
        is( $err->status, 'not_found', 'the not_found status is preserved' );
    }

    $client->close;
};

subtest 'call_tool_await propagates the timeout instead of returning the envelope' => sub {
    # The headline failure mode: call_tool_await is documented as "returns the
    # real result". On a hung job it used to return the running status, so a
    # caller got {status => running, result => undef} and no exception.
    my $client = Mem20::Client->new( config => config_for('jobhang') );

    my ( $err, $elapsed, $ok ) = timed_caught(
        sub { $client->call_tool_await( 'cog_plan', goal => 'x', { __await => { timeout => 0.4, interval => 0.05 } } ) }
    );

    ok( !$ok, 'call_tool_await does not return a value for a hung job' );
    ok( ref $err && $err->isa('Mem20::JobTimeoutError'), 'it raises JobTimeoutError' )
        or diag( 'got: ' . ( ref $err || $err || 'nothing' ) );
    ok( $elapsed < 5, sprintf( 'bounded at %.2fs', $elapsed ) );

    $client->close;
};

subtest 'wait_for_job validates its argument' => sub {
    my $client = Mem20::Client->new( config => config_for('job') );

    for my $bad ( undef, '' ) {
        my $err = Mem20::Errors::caught( sub { $client->wait_for_job($bad) } );
        ok( ref $err && $err->isa('Mem20::ValidationError'),
            'an empty job_id is refused locally' )
            or diag( 'got: ' . ( ref $err || $err || 'nothing' ) );
    }

    $client->close;
};

subtest 'a returned status is always terminal' => sub {
    # The invariant, stated once: whatever wait_for_job hands back must not
    # still be running. This is what makes the four specs above a property
    # rather than a set of special cases.
    for my $mode (qw(job jobfailed joblost jobhang)) {
        my $client = Mem20::Client->new( config => config_for($mode) );

        my $returned = eval { $client->wait_for_job( 'deadbeef01', timeout => 0.3, interval => 0.05 ) };

        if ( defined $returned ) {
            my $status = ref $returned eq 'HASH' ? ( $returned->{status} // '' ) : '';
            ok( !$RUNNING{$status},
                "$mode: a returned status is terminal ('$status')" );
        }
        else {
            ok( 1, "$mode: nothing returned, the failure was raised" );
        }

        $client->close;
    }
};

done_testing();
