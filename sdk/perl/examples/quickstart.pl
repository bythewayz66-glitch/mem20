#!/usr/bin/env perl
# Store a grounded fact, read it back, and confirm the live tool surface.
#
#   perl -Ilib examples/quickstart.pl [/path/to/mem20]
#
# The path argument is the mem20 CHECKOUT ROOT (the directory containing
# mcp/), because the server is run as `python mcp/mcp_server.py` and imports
# its siblings by script-directory name.

use strict;
use warnings;
use FindBin ();
use lib "$FindBin::Bin/../lib";

use Mem20;

my $checkout = $ARGV[0] // ($ENV{MEM20_CWD} // '/opt/mem20');
my $python   = $ENV{MEM20_PYTHON};    # e.g. /opt/mem20/.venv/bin/python

Mem20::configure(sub {
    my $c = shift;
    $c->cwd($checkout);         # the directory containing mcp/
    $c->timeout(60);
    # mem20 needs mcp/pydantic/anyio (plus aiohttp, which its requirements.txt
    # omits). If `python3` on PATH is not that interpreter, point at the venv
    # one with MEM20_PYTHON.
    $c->server_command( [ $python, 'mcp/mcp_server.py' ] ) if $python;
});

my $client = Mem20::client;

# epistemic_status is REQUIRED and is the point of the product: it records how
# the claim was learned, so grounded facts and guesses never mix.
$client->memory_store(
    content          => 'prod runs build 4127',
    category         => 'project',
    tags             => [ 'prod', 'build' ],
    epistemic_status => 'observed',
);
print "stored one fact\n";

my $hits = $client->memory_recall( query => 'what build is prod on', limit => 5 );
print "recall returned:\n", $client->text($hits), "\n";

my $surface = $client->verify_surface;
printf "surface: %d tools (SDK compiled for %d), %d domains, ok=%d\n",
    $surface->{tools}, $surface->{expected_tools}, $surface->{domains}, $surface->{ok};

$client->close;
