#!/usr/bin/env perl
# A minimal mem20-compatible MCP server, used by the SDK tests.
#
# It exists so the transport and client specs exercise the REAL code path:
# a child process, real pipes, real JSON-RPC framing, real EOF handling. A
# mocked transport would pass even if the framing were wrong.
#
# Behaviour is driven by the first argument so a test can ask for a specific
# failure mode without needing a second script:
#
#   ok          normal operation
#   error       every tool call answers with a JSON-RPC error object
#   noisy       writes a large amount on stderr before answering (the
#               stderr-pipe-deadlock case)
#   crash       exits immediately without answering
#   garbage     answers with unparseable text instead of JSON
#   silent      answers initialize/tools/list but never answers tools/call
#               (the timeout path, and the blocking-stderr-drain hang)
#   iserror     tools/call answers with result.isError = true
#   softerror   tools/call answers isError = false but text begins "Error"
#   job         cog_plan returns a background-job envelope; job_status walks
#               running -> running -> ok
#   jobhang     cog_plan returns a job envelope; job_status answers `running`
#               for ever (a job that never reaches a terminal state)
#   jobfailed   cog_plan returns a job envelope; job_status goes straight to
#               `error` with an error string, the way a raised job does
#   joblost     cog_plan returns a job envelope; job_status answers `not_found`,
#               which is what mem20 sends for a job_id it does not know
#
# The failure shapes mirror what mem20 3.0.0 actually emits; see
# sdk/perl/AUDIT.md for the raw transcripts that established them.
#
# The job status vocabulary is taken from mcp/server.py, not invented:
# _run_job() sets "ok" on success and "error" on failure, _spawn_job() starts at
# "running", and _job_status() answers "not_found" for an unknown job_id. There
# is no finished "done"/"complete"/"failed" spelling.

use strict;
use warnings;
use JSON::PP ();

my $MODE = $ARGV[0] // 'ok';

# The tools mem20 answers with a job envelope. Copied from
# Mem20MCPServer.LONG_RUNNING_TOOLS in mcp/server.py; t/95-jobs.t asserts this
# copy still matches the server's literal when MEM20_MCP_DIR is set.
my %LONG_RUNNING = map { $_ => 1 } qw(
    imagination_concept imagination_dream imagination_critique
    imagination_simulate imagination_counterfactual imagination_recombine
    imagination_model imagination_visualize
    cog_process cog_chain cog_reason cog_plan cog_reflect
    tot_reason tot_diagnose tot_modeling
    beam_search least_to_most react_reason
    theory_of_mind_simulate theory_of_mind_perspective
    self_model_reflect memory_auto_consolidate
    cognitive_substrate
);

$\ = "\n";
$| = 1;

my $json = JSON::PP->new->utf8->canonical;

# A deliberately small but structurally faithful tool list. memory_store
# carries the real inputSchema's required list, because the client validates
# required arguments against the advertised schema.
my @TOOLS = (
    {
        name        => 'memory_store',
        description => 'Store a grounded fact',
        inputSchema => {
            type       => 'object',
            properties => {
                content          => { type => 'string' },
                category         => {
                    type    => 'string',
                    enum    => [ 'user_pref', 'project', 'tool', 'general' ],
                    default => 'general',
                },
                tags             => { type => 'string', default => '' },
                epistemic_status => {
                    type => 'string',
                    enum => [ 'observed', 'inferred', 'imagined', 'user_stated',
                              'hypothesis', 'agent_generated', 'unlabeled' ],
                },
            },
            required => [ 'content', 'epistemic_status' ],
        },
    },
    {
        name        => 'memory_recall',
        description => 'Search stored facts',
        inputSchema => {
            type       => 'object',
            properties => {
                query    => { type => 'string' },
                category => { type => 'string', enum => [ 'user_pref', 'project', 'tool', 'general' ], default => '' },
                limit    => { type => 'integer', default => 10, minimum => 1, maximum => 50 },
            },
            required => [ 'query' ],
        },
    },
    { name => 'memory_status', description => 'Store health' },
    {
        name        => 'cog_plan',
        description => 'Plan a goal',
        inputSchema => {
            type       => 'object',
            properties => { goal => { type => 'string' } },
            required   => ['goal'],
        },
    },
    {
        name        => 'job_status',
        description => 'Check a background job',
        inputSchema => {
            type       => 'object',
            properties => { job_id => { type => 'string' } },
            required   => ['job_id'],
        },
    },
    # The long-running surface. Listed individually so a spec can drive any
    # member of LONG_RUNNING_TOOLS, not only cog_plan.
    map {
        {
            name        => $_,
            description => "Long-running tool $_",
            inputSchema => { type => 'object', properties => { goal => { type => 'string' } } },
        }
    } sort keys %LONG_RUNNING,
);

# NOT `send`: that is a CORE function (socket send), and defining a sub with
# that name shadows it in a way that produces surprising action-at-a-distance.
sub emit {
    my ($payload) = @_;
    print $json->encode($payload);
    return;
}

# One tool result envelope. `is_error` defaults to false, which is what mem20
# sends for a tool-level failure too.
sub tool_result {
    my ( $text, $is_error ) = @_;
    return {
        content => [ { type => 'text', text => $text } ],
        isError => $is_error ? JSON::PP::true : JSON::PP::false,
    };
}

if ($MODE eq 'crash') {
    exit 0;
}

if ($MODE eq 'noisy') {
    # More than a pipe buffer (64KiB) of stderr. If the client only reads
    # stdout, this write blocks, the server never reaches its first reply, and
    # the client hangs until its timeout.
    print STDERR 'x' x 200_000;
}

my $job_polls = 0;

# Per-job poll counters. A single global counter would let one job's polls
# advance another's, so a test driving several tools in sequence could see a
# job "complete" without ever having been polled.
my %POLLS_FOR;

while (defined(my $line = <STDIN>)) {
    chomp $line;
    next if $line =~ /^\s*$/;

    my $message = eval { $json->decode($line) };
    if ($@) {
        emit( {
            jsonrpc => '2.0',
            id      => undef,
            error   => { code => -32700, message => 'parse error' },
        } );
        next;
    }

    my $method = $message->{method} // '';
    my $id     = $message->{id};

    # Notifications carry no id and get no reply.
    next if !defined $id;

    if ($MODE eq 'garbage') {
        print "this is not json\n";
        next;
    }

    if ($method eq 'initialize') {
        emit( {
            jsonrpc => '2.0',
            id      => $id,
            result  => {
                protocolVersion => '2025-06-18',
                serverInfo      => { name => 'fake-mem20', version => '3.0.0' },
                capabilities    => { tools => {} },
            },
        } );
        next;
    }

    if ($method eq 'tools/list') {
        emit( { jsonrpc => '2.0', id => $id, result => { tools => \@TOOLS } } );
        next;
    }

    if ($method eq 'tools/call') {
        my $name = $message->{params}{name}      // '';
        my $args = $message->{params}{arguments} // {};

        # Start and never answer: exercises timeout and the stderr drain.
        if ($MODE eq 'silent') {
            print STDERR "silent mode: no reply coming\n";
            next;
        }

        if ($MODE eq 'error') {
            emit( {
                jsonrpc => '2.0',
                id      => $id,
                error   => {
                    code    => -32602,
                    message => 'invalid params (deliberate)',
                    data    => { tool => $name },
                },
            } );
            next;
        }

        if ($MODE eq 'iserror') {
            emit( {
                jsonrpc => '2.0',
                id      => $id,
                result  => tool_result( "Error: Unknown tool '$name'", 1 ),
            } );
            next;
        }

        if ($MODE eq 'softerror') {
            # Exactly mem20's tool-internal failure shape: a protocol SUCCESS
            # whose text begins "Error".
            emit( {
                jsonrpc => '2.0',
                id      => $id,
                result  => tool_result( "Error storing memory: Invalid epistemic_status 'x'", 0 ),
            } );
            next;
        }

        if ($name eq 'memory_store') {
            # Echo the arguments back so the test can assert on what was sent,
            # which is how the tags-array-vs-string behaviour is verified.
            my $reply = $json->encode( { stored => $args } );
            emit( { jsonrpc => '2.0', id => $id, result => tool_result($reply) } );
            next;
        }

        if ($name eq 'memory_recall') {
            emit( {
                jsonrpc => '2.0',
                id      => $id,
                result  => {
                    content => [
                        { type => 'text', text => 'the sky is blue' },
                        { type => 'text', text => 'water is wet' },
                    ],
                },
            } );
            next;
        }

        if ($name eq 'memory_status') {
            emit( { jsonrpc => '2.0', id => $id, result => tool_result('ok') } );
            next;
        }

        if ($name eq 'cog_plan') {
            if ($MODE =~ /^job/) {
                emit( {
                    jsonrpc => '2.0',
                    id      => $id,
                    result  => tool_result( $json->encode( {
                        job_id => 'deadbeef01',
                        status => 'running',
                        tool   => 'cog_plan',
                        poll   => 'job_status',
                        wait   => 'job_wait',
                    } ) ),
                } );
                next;
            }
            emit( { jsonrpc => '2.0', id => $id, result => tool_result('planned inline') } );
            next;
        }

        # Every other long-running tool answers with the same envelope shape,
        # so a test can drive the whole LONG_RUNNING_TOOLS set rather than one
        # representative. The job_id is derived from the tool name so a test
        # can tell which tool a status belongs to.
        if ( $MODE =~ /^job/ && $LONG_RUNNING{$name} ) {
            emit( {
                jsonrpc => '2.0',
                id      => $id,
                result  => tool_result( $json->encode( {
                    job_id => "job-$name",
                    status => 'running',
                    tool   => $name,
                    poll   => 'job_status',
                    wait   => 'job_wait',
                } ) ),
            } );
            next;
        }

        if ($name eq 'job_status') {
            $job_polls++;
            my $job_id = $args->{job_id};
            my $polls  = ++$POLLS_FOR{$job_id};

            # A job that never finishes. Deliberately answers `running` with no
            # end, so the only way out of a poll loop is the caller's deadline.
            if ($MODE eq 'jobhang') {
                emit( {
                    jsonrpc => '2.0',
                    id      => $id,
                    result  => tool_result( $json->encode( {
                        job_id => $job_id, status => 'running',
                    } ) ),
                } );
                next;
            }

            # A job whose handler raised: mem20 sets status "error" and an
            # error string, with result left null.
            if ($MODE eq 'jobfailed') {
                emit( {
                    jsonrpc => '2.0',
                    id      => $id,
                    result  => tool_result( $json->encode( {
                        job_id => $job_id,
                        status => 'error',
                        tool   => 'cog_plan',
                        result => undef,
                        error  => 'RuntimeError: cog_plan raised',
                    } ) ),
                } );
                next;
            }

            # mem20 answers not_found for a job_id it never issued.
            if ($MODE eq 'joblost') {
                emit( {
                    jsonrpc => '2.0',
                    id      => $id,
                    result  => tool_result( $json->encode( {
                        job_id => $job_id, status => 'not_found',
                    } ) ),
                } );
                next;
            }

            # The normal walk: running, running, then ok with a real payload.
            # The payload names the tool the job belongs to, so a test can
            # prove the result it received came from the job it started rather
            # than from a stale or shared status.
            my $tool = $job_id =~ /^job-(.+)$/ ? $1 : 'cog_plan';
            my $status = $polls >= 3
                ? {
                    job_id => $job_id,
                    status => 'ok',
                    tool   => $tool,
                    result => "the plan for $tool",
                }
                : { job_id => $job_id, status => 'running', tool => $tool };
            emit( { jsonrpc => '2.0', id => $id, result => tool_result( $json->encode($status) ) } );
            next;
        }

        emit( {
            jsonrpc => '2.0',
            id      => $id,
            error   => { code => -32601, message => "unknown tool: $name" },
        } );
        next;
    }

    emit( {
        jsonrpc => '2.0',
        id      => $id,
        error   => { code => -32601, message => "unknown method: $method" },
    } );
}

exit 0;
