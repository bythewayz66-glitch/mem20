#!/usr/bin/env perl
# Store a fact, then read it back.
#
#   perl -Ilib examples/quickstart.pl [/path/to/mem20]

use strict;
use warnings;
use FindBin ();
use lib "$FindBin::Bin/../lib";

use Mem20;

my $repo = $ARGV[0] // ($ENV{MEM20_CWD} // '/opt/mem20');

Mem20::configure(sub {
    my $c = shift;
    $c->cwd($repo);
    $c->timeout(60);
});

my $client = Mem20::client;

$client->memory_store(
    content  => 'prod runs build 4127',
    category => 'deploys',
    tags     => [ 'prod', 'build' ],
);
print "stored one fact\n";

my $hits = $client->memory_recall( query => 'what build is prod on', limit => 5 );
my $text = Mem20::Client::text($hits);

print "recall returned:\n$text\n";

$client->close;
