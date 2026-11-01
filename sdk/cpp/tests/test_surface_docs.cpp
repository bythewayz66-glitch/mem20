// sdk/cpp/tests/test_surface_docs.cpp
//
// Documentation drift guard for the SDK's published tool/domain surface.
//
// `test_live_surface` proves the number against a running server, but it can
// only run where python3 + the mem20 server exist, and it never looks at prose.
// The number that actually ships is the one a reader sees in README.md, so this
// test greps the documents for it and fails the suite when they disagree with
// mem20::surface -- no server, no python3, always runnable.
//
// What it checks, in order:
//   1. surface.hpp still spells the literals (a rename or a typo in the header
//      cannot slip past: the file must literally say `kToolCount = 270`).
//   2. The header's derived constants agree with version.hpp's server baseline.
//   3. sdk/cpp/README.md states the summary string ("270 tools across 27
//      domains") verbatim.
//   4. docs/sdk/cpp/README.md states it too.
//   5. Neither document re-publishes a retired figure (257 tools / 26 domains /
//      268 tools) outside an explicit "retired" note.
//
// Exit contract:
//   0  -> documented surface matches the header
//   1  -> drift (each violation printed)
//   77 -> SKIPPED: a path CMake was supposed to provide does not exist
//
// Requires C++17.

#include "mem20/surface.hpp"
#include "mem20/version.hpp"

#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#ifndef MEM20_TEST_SURFACE_HEADER
#error "MEM20_TEST_SURFACE_HEADER must be defined by CMakeLists.txt"
#endif
#ifndef MEM20_TEST_SDK_README
#error "MEM20_TEST_SDK_README must be defined by CMakeLists.txt"
#endif
#ifndef MEM20_TEST_DOCS_README
#error "MEM20_TEST_DOCS_README must be defined by CMakeLists.txt"
#endif

namespace {

constexpr int kExitOk = 0;
constexpr int kExitFail = 1;
constexpr int kExitSkip = 77;

std::vector<std::string> g_failures;

void violation(const std::string& what) { g_failures.push_back(what); }

bool read_file(const std::string& path, std::string& out) {
  std::ifstream in(path.c_str(), std::ios::in | std::ios::binary);
  if (!in) return false;
  std::ostringstream buf;
  buf << in.rdbuf();
  out = buf.str();
  return true;
}

// True when `needle` appears anywhere in `haystack`.
bool contains(const std::string& haystack, const std::string& needle) {
  return haystack.find(needle) != std::string::npos;
}

// Split into lines so a retired figure can be judged in its own context: the
// number is fine on a line that says it is retired, and drift anywhere else.
std::vector<std::string> lines_of(const std::string& text) {
  std::vector<std::string> lines;
  std::string current;
  for (char raw : text) {
    const unsigned char c = static_cast<unsigned char>(raw);
    if (c == '\n') {
      lines.push_back(current);
      current.clear();
    } else if (c != '\r') {
      current.push_back(static_cast<char>(c));
    }
  }
  if (!current.empty()) lines.push_back(current);
  return lines;
}

bool mentions_retirement(const std::string& line) {
  return contains(line, "retired") || contains(line, "Retired") ||
         contains(line, "RETIRED");
}

// True when `number` occurs in `line` as a whole token, so `26` matches
// "26 domains" but not "2026" or "1.26".
bool contains_number(const std::string& line, const std::string& number) {
  std::size_t at = line.find(number);
  while (at != std::string::npos) {
    const bool left_ok =
        at == 0 || !(std::isdigit(static_cast<unsigned char>(line[at - 1])) ||
                     line[at - 1] == '.');
    const std::size_t after = at + number.size();
    const bool right_ok =
        after >= line.size() ||
        !(std::isdigit(static_cast<unsigned char>(line[after])) ||
          line[after] == '.');
    if (left_ok && right_ok) return true;
    at = line.find(number, at + 1);
  }
  return false;
}

// A retired tool count or domain count must not appear on a line that does not
// also say it is retired. The check is deliberately narrow -- a retired *tool*
// number only counts when the line also talks about tools, and likewise for
// domains -- so ordinary prose ("270 tools across 27 domains") is never caught
// by a bare number.
void check_retired_figures(const std::string& label, const std::string& text) {
  const std::vector<std::string> lines = lines_of(text);
  for (std::size_t i = 0; i < lines.size(); ++i) {
    const std::string& line = lines[i];
    // Prose wraps, so "Retired" can sit on the line above the numbers. Judge
    // the number against its own line plus the one before it.
    const std::string context =
        (i == 0) ? line : (lines[i - 1] + " " + line);
    if (mentions_retirement(context)) continue;

    if (contains(line, "tools")) {
      for (const char* retired : {"257", "268", "270 / 26"}) {
        if (contains_number(line, retired)) {
          violation(label + ": states the retired tool count " + retired +
                    " without marking it retired -> " + line);
        }
      }
    }
    if (contains(line, "domains")) {
      for (const char* retired : {"26"}) {
        if (contains_number(line, retired)) {
          violation(label + ": states the retired domain count " + retired +
                    " without marking it retired -> " + line);
        }
      }
    }
  }
}

}  // namespace

int main() {
  const std::string expected = mem20::surface::summary();
  std::cout << "mem20 C++ SDK surface docs test\n"
            << "  expected surface : " << expected << "\n";

  // --- 1. the header must spell the literals -------------------------------
  std::string header;
  if (!read_file(MEM20_TEST_SURFACE_HEADER, header)) {
    std::cerr << "SKIP: surface header not found at "
              << MEM20_TEST_SURFACE_HEADER << "\n";
    return kExitSkip;
  }
  const std::string literal =
      "kToolCount = " + std::to_string(mem20::surface::kToolCount);
  if (!contains(header, literal)) {
    violation("surface.hpp does not literally declare `" + literal + "`");
  }
  const std::string domain_literal =
      "kDomainCount == " + std::to_string(mem20::surface::kDomainCount);
  if (!contains(header, domain_literal)) {
    violation("surface.hpp does not pin `" + domain_literal + "` in a "
              "static_assert");
  }

  // --- 2. the header and version.hpp must agree on the server baseline -----
  if (std::string(mem20::surface::kServerVersion) !=
      std::string(mem20::kServerBaseline)) {
    violation(std::string("server baseline disagrees: surface.hpp says ") +
              mem20::surface::kServerVersion + ", version.hpp says " +
              mem20::kServerBaseline);
  }

  // --- 3/4. both READMEs must state the summary ----------------------------
  struct Doc {
    const char* label;
    const char* path;
  };
  const Doc docs[] = {
      {"sdk/cpp/README.md", MEM20_TEST_SDK_README},
      {"docs/sdk/cpp/README.md", MEM20_TEST_DOCS_README},
  };
  for (const Doc& doc : docs) {
    std::string text;
    if (!read_file(doc.path, text)) {
      std::cerr << "SKIP: " << doc.label << " not found at " << doc.path
                << "\n";
      return kExitSkip;
    }
    if (!contains(text, expected)) {
      violation(std::string(doc.label) + ": does not state \"" + expected +
                "\"");
    }
    // --- 5. and must not re-publish a retired count -----------------------
    check_retired_figures(doc.label, text);
  }

  if (!g_failures.empty()) {
    for (const std::string& f : g_failures) {
      std::cerr << "FAIL: " << f << "\n";
    }
    std::cerr << "FAIL: " << g_failures.size()
              << " surface documentation violation(s)\n";
    return kExitFail;
  }

  std::cout << "PASS: surface.hpp, version.hpp and both READMEs agree on "
            << expected << "\n";
  return kExitOk;
}
