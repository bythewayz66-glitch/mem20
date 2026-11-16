use strict;
use warnings;

use Test::More;
use File::Basename ();
use File::Spec ();
use Mem20::Version ();
use Mem20::Surface ();

# Surface drift guard.
#
# The Perl SDK states its tool and domain counts in several places that are
# edited by different people at different times: the generated manifest
# (Mem20::Surface), the constants in Mem20::Version, the README, the POD in
# Mem20::Client, and AUDIT.md. Historically those drifted apart (the Ruby gem
# quoted 268, 270 and 257 for the same surface in four files), and a stale
# number in a README is invisible to every other test in this distribution
# because nothing else reads prose.
#
# This file is the guard. It fails when:
#
#   1. the documented count and the generated manifest disagree;
#   2. any doc still quotes a retired count (257 / 268 / 269 / 270 / 271 /
#      272 / 306 / 311);
#   3. a doc states a domain count other than the manifest's;
#   4. the manifest is internally inconsistent (names vs map vs counts);
#   5. the checked-in manifest is stale against the repository's surface files.
#
# It deliberately does NOT assert the absolute value against the server -- that
# is t/90-live-server.t's job, and it needs a live server. This test is
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

cmp_ok( $TOOLS, '>=', $DOMAINS, 'there are at least as many tools as domains' );
cmp_ok( $DOMAINS, '>=', 10, 'the domain count is not a typo-sized number' );

# --- the constants come from the generated manifest --------------------------

# Version.pm must re-export the manifest, not carry its own literals. A hand
# edit to Version.pm that disagreed with Surface.pm would otherwise pass every
# doc check below while the SDK reported two different surfaces.
is( $TOOLS, $Mem20::Surface::TOOL_COUNT,
    'SURFACE_TOOL_COUNT is the manifest tool count' );
is( $DOMAINS, $Mem20::Surface::DOMAIN_COUNT,
    'SURFACE_DOMAIN_COUNT is the manifest domain count' );

# --- the manifest is internally consistent -----------------------------------

is( scalar @Mem20::Surface::TOOL_NAMES, $TOOLS,
    'the manifest name list has exactly TOOL_COUNT entries' );

is( scalar( keys %Mem20::Surface::TOOL_DOMAIN ), $TOOLS,
    'the tool-to-domain map covers every tool' );

is( scalar @Mem20::Surface::DOMAIN_NAMES, $DOMAINS,
    'the manifest domain list has exactly DOMAIN_COUNT entries' );

my %unique = map { $_ => 1 } @Mem20::Surface::TOOL_NAMES;
is( scalar keys %unique, $TOOLS, 'every tool name in the manifest is unique' );

# Every tool's domain must be a real domain, and the reverse map must agree.
my @bad_domain = grep { !defined $Mem20::Surface::TOOL_DOMAIN{$_} } @Mem20::Surface::TOOL_NAMES;
is_deeply( \@bad_domain, [], 'every tool has a domain' )
    or diag("tools without a domain: @bad_domain");

my %domain_names = map { $_ => 1 } @Mem20::Surface::DOMAIN_NAMES;
my @unknown_domain = grep { !$domain_names{ $Mem20::Surface::TOOL_DOMAIN{$_} } }
    @Mem20::Surface::TOOL_NAMES;
is_deeply( \@unknown_domain, [], 'every tool domain is in the domain list' )
    or diag("tools with an unknown domain: @unknown_domain");

# The reverse map is built from the forward one, so the two must partition the
# same set. A mismatch means one of them was edited by hand.
my $sum = 0;
$sum += scalar( Mem20::Surface->tools_in($_) ) for @Mem20::Surface::DOMAIN_NAMES;
is( $sum, $TOOLS, 'the per-domain tool counts sum to the total' );

# --- the manifest is not stale ----------------------------------------------

# xt/gen-surface.pl --check regenerates in memory and compares. It needs the
# repository's docs/surface.json and web/src/data/tools.json, which are NOT in
# the CPAN tarball, so this is skipped when the SDK is installed standalone.
my $generator    = File::Spec->catfile( $ROOT, 'xt', 'gen-surface.pl' );
my $repo_root    = File::Spec->rel2abs( File::Spec->catdir( $ROOT, File::Spec->updir, File::Spec->updir ) );
my $surface_json = File::Spec->catfile( $repo_root, 'docs', 'surface.json' );

SKIP: {
    skip 'xt/gen-surface.pl not present (installed distribution)', 1 unless -f $generator;
    skip 'docs/surface.json not present (installed distribution)', 1 unless -f $surface_json;

    my $out = `"$^X" "$generator" --check 2>&1`;
    my $rc  = $? >> 8;
    is( $rc, 0, 'the checked-in manifest matches the repository surface files' )
        or diag($out);
}

# --- every doc that states a count must state THIS count ---------------------

my @DOCS = grep { -f File::Spec->catfile( $ROOT, $_ ) }
    qw( README.md AUDIT.md lib/Mem20/Version.pm lib/Mem20/Client.pm lib/Mem20/Surface.pm );

ok( @DOCS >= 4, 'found the documents to check' ) or diag("root=$ROOT");

my %body;
for my $doc (@DOCS) {
    my $path = File::Spec->catfile( $ROOT, $doc );
    open my $fh, '<', $path or do { fail("cannot read $doc: $!"); next };
    local $/;
    $body{$doc} = <$fh>;
    close $fh;
}

# Retired counts. 257 was the pre-3.0 surface, 268 was the domain-tools-only
# figure that the Ruby gem once mistook for the total, 270 was the pre-temporal
# surface, 272 was the wave-1 surface, 306 was the pre-temporal count, 311 was
# the 3.1.2 surface this SDK shipped 0.2.0 against, and 269/271 are off-by-one
# neighbours that a hand edit produces. None of them may appear as a tool count.
my @RETIRED = ( 257, 268, 269, 270, 271, 272, 306, 311 );

for my $doc ( sort keys %body ) {
    for my $n (@RETIRED) {
        unlike(
            $body{$doc},
            qr/\b$n\b(?=[^\n]{0,40}\b(?:tools?|tool surface)\b)/,
            "$doc does not quote the retired $n-tool surface"
        );
    }

    # Any "<N> tools across <M> domains" phrase must use both live constants.
    while ( $body{$doc} =~ /\b(\d+)\s+tools?\s+across\s+(\d+)\s+domains?\b/g ) {
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
    qr/\Q$TOOLS\E tools across \Q$DOMAINS\E domains/,
    "Client POD states $TOOLS tools across $DOMAINS domains"
);

# Version.pm: the constants are re-exported, so the POD beside them must not
# contradict them.
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

# --- the code that consumes the manifest -------------------------------------

# verify_surface must read the manifest, not a literal of its own. A hardcoded
# count inside Client.pm would pass every doc check above while silently
# ignoring a manifest bump.
my $client_src = $body{'lib/Mem20/Client.pm'};
my ($verify_body) = $client_src =~ /^sub verify_surface \{(.*?)^\}/ms;
ok( $verify_body, 'found the verify_surface body in Client.pm' );

SKIP: {
    skip 'verify_surface body not found', 3 unless $verify_body;

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
        qr/Mem20::Surface->diff/,
        'verify_surface delegates to the generated manifest'
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

    unlike( $live, qr/expected_tools\s*=>\s*\d+/, 'live test does not hardcode expected_tools' );
    unlike( $live, qr/domains\s*=>\s*\d+/,        'live test does not hardcode domains' );
}

done_testing();
