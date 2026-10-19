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

use strict;
use warnings;
use JSON::PP ();

my $MODE = $ARGV[0] // 'ok';

$\ = "\n";
$| = 1;

my $json = JSON::PP->new->utf8->canonical;

# A deliberately small but structurally faithful tool list.
my @TOOLS = (
    { name => 'memory_store',  description => 'Store a fact' },
    { name => 'memory_recall', description => 'Search stored facts' },
    { name => 'memory_status', description => 'Store health' },
    { name => 'cog_plan',      description => 'Plan a goal' },
);

# NOT `send`: that is a CORE function (socket send), and defining a sub with
# that name shadows it in a way that produces surprising action-at-a-distance.
sub emit {
    my ($payload) = @_;
    print $json->encode($payload);
    return;
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

        if ($name eq 'memory_store') {
            # Echo the arguments back so the test can assert on what was sent,
            # which is how the tags-array-vs-string behaviour is verified.
            my $reply = $json->encode( { stored => $args } );
            emit( {
                jsonrpc => '2.0',
                id      => $id,
                result  => { content => [ { type => 'text', text => $reply } ] },
            } );
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
            emit( {
                jsonrpc => '2.0',
                id      => $id,
                result  => { content => [ { type => 'text', text => 'ok' } ] },
            } );
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
