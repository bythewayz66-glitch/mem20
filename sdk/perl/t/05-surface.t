use strict;
use warnings;

use Test::More;
use File::Basename ();
use File::Spec ();
use Mem20::Version ();

# Surface drift guard.
#
# The Perl SDK states its tool and domain counts in four places that are edited
# by different people at different times: the constants in Mem20::Version, the
# README, the POD in Mem20::Client, and AUDIT.md. Historically those drifted
# apart (the Ruby gem quoted 268, 270 and 257 for the same surface in four
# files), and a stale number in a README is invisible to every other test in
# this distribution because nothing else reads prose.
#
# This file is the guard. It fails when:
#
#   1. the documented count and $Mem20::Version::SURFACE_TOOL_COUNT disagree;
#   2. any doc still quotes a retired count (257 / 268 / 269 / 271);
#   3. a doc states a domain count other than SURFACE_DOMAIN_COUNT;
#   4. the constants themselves are internally inconsistent.
#
# It deliberately does NOT assert the absolute value 270 against the server --
# that is t/90-live-server.t's job, and it needs a live server. This test is
# hermetic: it only checks that the SDK agrees with itself, so it runs on any
# machine with a stock perl.

# Resolve the distribution root from THIS file, not from the current working
# directory. CI runs `prove -Isdk/perl/lib sdk/perl/t/*.t` from the repository
# root, while a developer runs `prove -Ilib t/` from sdk/perl; a cwd-based root
# silently produced undef file bodies (and 10 false failures) under CI.
my $ROOT = File::Spec->rel2abs(
    File::Spec->catdir( File::Basename::dirname( File::Spec->rel2abs(__FILE__) ), File::Spec->updir )
);

my $TOOLS   = $Mem20::Version::SURFACE_TOOL_COUNT;
my $DOMAINS = $Mem20::Version::SURFACE_DOMAIN_COUNT;

# --- the constants are sane --------------------------------------------------

ok( defined $TOOLS   && $TOOLS   =~ /^\d+$/ && $TOOLS   > 0, "SURFACE_TOOL_COUNT is a positive integer ($TOOLS)" );
ok( defined $DOMAINS && $DOMAINS =~ /^\d+$/ && $DOMAINS > 0, "SURFACE_DOMAIN_COUNT is a positive integer ($DOMAINS)" );

# A domain cannot expose fewer than one tool, and the surface is not one giant
# domain. These bounds are loose on purpose: they catch a transposed digit or a
# constant set to 0, not a legitimate upstream change.
cmp_ok( $TOOLS, '>=', $DOMAINS, 'there are at least as many tools as domains' );
cmp_ok( $DOMAINS, '>=', 10, 'the domain count is not a typo-sized number' );

# --- every doc that states a count must state THIS count ---------------------

my @DOCS = grep { -f File::Spec->catfile( $ROOT, $_ ) }
    qw( README.md AUDIT.md lib/Mem20/Version.pm lib/Mem20/Client.pm );

ok( @DOCS >= 3, 'found the documents to check' ) or diag("root=$ROOT");

my %body;
for my $doc (@DOCS) {
    my $path = File::Spec->catfile( $ROOT, $doc );
    open my $fh, '<', $path or do { fail("cannot read $doc: $!"); next };
    local $/;
    $body{$doc} = <$fh>;
    close $fh;
}

# Retired counts. 257 was the pre-3.0 surface, 268 was the domain-tools-only
# figure that the Ruby gem once mistook for the total, 269/271 are off-by-one
# neighbours that a hand edit produces, and 270 is the surface this SDK shipped
# as 0.2.0 -- retired by the RM-239/RM-052 merges that took it to 272.
#
# 270 was MISSING from this list until 0.2.1, which is exactly how the drift got
# through: t/90-live-server.t still asserted `expected_tools, 270` as a literal,
# the live suite failed against the real server, and this guard stayed green
# because 270 was not a retired number and the literal used a comma rather than
# `=>`. Both holes are closed below.
my @RETIRED = ( 257, 268, 269, 270, 271 );

# Strip fenced code blocks before looking for stale PROSE claims.
#
# A fenced block is evidence: a transcript, a command, a quoted failure line.
# AUDIT.md legitimately contains `expected: '270'` inside the transcript of the
# very failure this release fixes, and rewriting that to 272 would falsify the
# evidence. Prose must never claim a retired count; a quoted transcript may.
#
# This is deliberately narrow -- only ``` fences are stripped, so a stale claim
# in a heading, a table or a sentence is still caught.
sub prose_only {
    my ($text) = @_;
    $text =~ s/^```.*?^```//msg;
    return $text;
}

for my $doc ( sort keys %body ) {
    my $prose = prose_only( $body{$doc} );

    for my $n (@RETIRED) {
        unlike(
            $prose,
            qr/\b$n\b(?=[^\n]{0,40}\b(?:tools?|tool surface)\b)/,
            "$doc does not quote the retired $n-tool surface in prose"
        );
    }

    # Any "<N> tools across <M> domains" phrase must use both live constants.
    while ( $prose =~ /\b(\d+)\s+tools?\s+across\s+(\d+)\s+domains?\b/g ) {
        my ( $t, $d ) = ( $1, $2 );
        is( $t, $TOOLS,   "$doc: '$t tools across $d domains' uses the live tool count" );
        is( $d, $DOMAINS, "$doc: '$t tools across $d domains' uses the live domain count" );
    }
}

# --- the specific places a reader actually looks -----------------------------

# README: the headline claim and the verify_surface example.
like(
    $body{'README.md'},
    qr/\Q$TOOLS\E-tool surface across \Q$DOMAINS\E domains/,
    "README headline states $TOOLS tools across $DOMAINS domains"
);
like(
    $body{'README.md'},
    qr/expected_tools\s*=>\s*\Q$TOOLS\E/,
    "README verify_surface example predicts expected_tools => $TOOLS"
);
like(
    $body{'README.md'},
    qr/domains\s*=>\s*\Q$DOMAINS\E/,
    "README verify_surface example predicts domains => $DOMAINS"
);

# POD: Mem20::Client documents verify_surface with the same pair.
like(
    $body{'lib/Mem20/Client.pm'},
    qr/\Q$TOOLS\E across \Q$DOMAINS\E domains/,
    "Client POD states $TOOLS across $DOMAINS domains"
);

# Version.pm: the constants are the source of truth, so the POD beside them
# must not contradict them.
like(
    $body{'lib/Mem20/Version.pm'},
    qr/SURFACE_TOOL_COUNT>\s*-\s*tools the SDK is compiled\s+against \(\Q$TOOLS\E\)/s,
    "Version POD states SURFACE_TOOL_COUNT ($TOOLS)"
);
like(
    $body{'lib/Mem20/Version.pm'},
    qr/SURFACE_DOMAIN_COUNT>\s*-\s*domain modules the server\s+registers \(\Q$DOMAINS\E\)/s,
    "Version POD states SURFACE_DOMAIN_COUNT ($DOMAINS)"
);

# AUDIT.md: the scope line and the section heading.
like(
    $body{'AUDIT.md'},
    qr/Target surface \*\*\Q$TOOLS\E tools across \Q$DOMAINS\E domains\*\*/,
    "AUDIT.md scope line states $TOOLS tools across $DOMAINS domains"
);
like(
    $body{'AUDIT.md'},
    qr/## 1\. The surface: \Q$TOOLS\E tools, \Q$DOMAINS\E domains/,
    "AUDIT.md section heading states $TOOLS tools, $DOMAINS domains"
);

# --- the code that consumes the constants ------------------------------------

# verify_surface must report the constants, not a literal of its own. A
# hardcoded 270 inside Client.pm would pass every doc check above while
# silently ignoring a constant bump.
#
# Scope the check to the sub body: the POD and the comments in the same file
# legitimately contain illustrative `domains => 27` text, and matching those
# would make this test fail for the wrong reason.
my $client_src = $body{'lib/Mem20/Client.pm'};
my ($verify_body) = $client_src =~ /^sub verify_surface \{(.*?)^\}/ms;
ok( $verify_body, 'found the verify_surface body in Client.pm' );

SKIP: {
    skip 'verify_surface body not found', 4 unless $verify_body;

    unlike(
        $verify_body,
        qr/expected_tools\s*=>\s*\d+/,
        'verify_surface does not hardcode expected_tools'
    );
    unlike(
        $verify_body,
        qr/domains\s*=>\s*\d+/,
        'verify_surface does not hardcode domains'
    );
    like(
        $verify_body,
        qr/expected_tools\s*=>\s*\$Mem20::Version::SURFACE_TOOL_COUNT/,
        'verify_surface reads SURFACE_TOOL_COUNT'
    );
    like(
        $verify_body,
        qr/domains\s*=>\s*\$Mem20::Version::SURFACE_DOMAIN_COUNT/,
        'verify_surface reads SURFACE_DOMAIN_COUNT'
    );
}

# --- the live test must not restate the numbers as literals ------------------

# t/90-live-server.t asserts against the constants; if someone "fixes" a live
# failure by editing a literal there, the guard should notice.
my $live_path = File::Spec->catfile( $ROOT, 't', '90-live-server.t' );
if ( -f $live_path ) {
    open my $fh, '<', $live_path or fail("cannot read t/90-live-server.t: $!");
    my $live = do { local $/; <$fh> };
    close $fh;

    # Match BOTH spellings a hardcoded expectation takes: the hashref form
    # (`expected_tools => 270`) and the assertion form
    # (`is( $surface->{expected_tools}, 270 )`). The original regex only caught
    # `=>`, so the comma form in t/90-live-server.t slipped past it.
    unlike( $live, qr/\bexpected_tools\}?\s*(?:=>|,)\s*\d+/,
        'live test does not hardcode expected_tools' );
    unlike( $live, qr/\bdomains\}?\s*(?:=>|,)\s*\d+/,
        'live test does not hardcode domains' );

    # ...and it must actually read the constants, so deleting the assertion is
    # not a way to make the two checks above pass.
    like( $live, qr/\$Mem20::Version::SURFACE_TOOL_COUNT/,
        'live test reads SURFACE_TOOL_COUNT' );
    like( $live, qr/\$Mem20::Version::SURFACE_DOMAIN_COUNT/,
        'live test reads SURFACE_DOMAIN_COUNT' );
}

done_testing();
