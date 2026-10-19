use strict;
use warnings;

use Test::More;
use Config ();

# Every module in the distribution must compile and load cleanly. A broken
# `use` line in any of them is invisible until something imports it, so this is
# the gate that catches it.

use_ok('Mem20');
use_ok('Mem20::Version');
use_ok('Mem20::Errors');
use_ok('Mem20::Config');
use_ok('Mem20::Client');
use_ok('Mem20::Transport::Stdio');

# The error hierarchy has to be a real hierarchy: callers catch Mem20::Error and
# expect every SDK error to match.
ok( Mem20::ConfigurationError->isa('Mem20::Error'),       'ConfigurationError isa Error' );
ok( Mem20::TransportError->isa('Mem20::Error'),          'TransportError isa Error' );
ok( Mem20::ToolError->isa('Mem20::Error'),               'ToolError isa Error' );
ok( !Mem20::ToolError->isa('Mem20::ConfigurationError'), 'ToolError is not a ConfigurationError' );
ok( !Mem20::Error->isa('Mem20::ToolError'),              'Error is not a ToolError' );

# Version constants exist and look like versions.
like( $Mem20::Version::VERSION,          qr/^\d+\.\d+\.\d+$/,      'SDK VERSION is semver' );
like( $Mem20::Version::SERVER_VERSION,   qr/^\d+\.\d+\.\d+/,       'SERVER_VERSION recorded' );
like( $Mem20::Version::PROTOCOL_VERSION, qr/^\d{4}-\d{2}-\d{2}$/,  'PROTOCOL_VERSION is a date revision' );

# --- no non-core dependencies ------------------------------------------------
#
# The point of this SDK is that it installs with nothing but core Perl. A `use
# LWP::UserAgent` added later would silently make the distribution
# uninstallable on a stock interpreter, so this asserts every `use` resolves to
# a module shipped with perl itself.

my %is_core = map { $_ => 1 } qw(strict warnings utf8 parent base constant overload);

# Everything else is checked against Module::CoreList, which is itself core.
# A hand-maintained allowlist would rot: JSON::PP, IPC::Open3, IO::Select,
# HTTP::Tiny and Time::HiRes are all core, and an allowlist that forgot them
# would fail the build for the wrong reason.
#
# The single-argument form is the right question here — is this module shipped
# with some perl core? Every module used has been core for far longer than the
# 5.20 floor in Makefile.PL.
use Module::CoreList ();

for my $module (qw(Mem20 Mem20::Version Mem20::Errors Mem20::Config Mem20::Client Mem20::Transport::Stdio)) {
    my $file = "$module.pm";
    $file =~ s{::}{/}g;

    my $path = $INC{$file};
    ok( $path, "$module resolved to a file" ) or next;

    open my $src, '<', $path or do { fail("cannot read $path: $!"); next };
    my @lines = <$src>;
    close $src;

    my @external = map {
        /^\s*use\s+([A-Za-z_][\w:]*)/ ? $1 : ()
    } grep { !/^\s*#/ } @lines;

    my @non_core = grep {
        !$is_core{$_} && $_ !~ /^Mem20/ && !Module::CoreList::is_core($_)
    } @external;

    is_deeply( \@non_core, [], "$module declares no non-core module" )
        or diag("non-core: @non_core");
}

done_testing();
