#pragma once

namespace mem20 {

inline constexpr const char* kSdkVersion = "4.0.0+ng";
inline constexpr const char* kProtocolVersion = "2025-06-18";
// Latest mem20 release cut at the HEAD this SDK release was verified against
// (VERSION / pyproject.toml `4.0.0+ng`). Kept equal to surface::kServerVersion by
// the surface_docs test.
inline constexpr const char* kServerBaseline = "4.0.0+ng";

}  // namespace mem20
