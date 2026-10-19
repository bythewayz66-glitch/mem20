use strict;
use warnings;

# Build script for the mem20 Perl SDK.
#
# Nothing but ExtUtils::MakeMaker, which ships with perl. There is no Alien::,
# no XS, and no non-core prerequisite: `perl Makefile.PL && make test` works on
# an air-gapped host.

use ExtUtils::MakeMaker;

WriteMakefile(
    NAME             => 'Mem20',
    VERSION_FROM     => 'lib/Mem20/Version.pm',
    ABSTRACT         => 'Perl SDK for the mem20 memory + cognition server',
    AUTHOR           => 'mem20 contributors',
    LICENSE          => 'mit',
    MIN_PERL_VERSION => '5.020',
    PREREQ_PM        => {
        # Only the test harness. The runtime is core-Perl only; see t/00-load.t,
        # which fails the build if a non-core module is ever imported.
        'Test::More' => '0',
    },
    TEST_REQUIRES    => {
        'Test::More' => '0',
    },
    META_MERGE       => {
        resources => {
            repository => 'https://github.com/bythewayz66-glitch/mem20',
            homepage   => 'https://github.com/bythewayz66-glitch/mem20',
        },
    },
    test => { TESTS => 't/*.t' },
);
