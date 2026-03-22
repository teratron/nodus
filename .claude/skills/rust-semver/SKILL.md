---
name: Rust SemVer
description: Guidelines and checklists for maintaining semantic versioning in Rust projects, including breaking change identification and mitigation strategies.
---

# Rust SemVer Skill

This skill provides comprehensive guidance on managing Semantic Versioning (SemVer) in Rust. Use this when planning API changes, performing refactors, or preparing for new releases to ensure backward compatibility or correctly identify breaking changes.

## Versioning Basics

**Version Format:** `MAJOR.MINOR.PATCH`

- **MAJOR** — incompatible API changes
- **MINOR** — backwards-compatible new features
- **PATCH** — backwards-compatible bug fixes

**0.y.z releases:** changes in `y` = major, changes in `z` = minor

## Change Categories

### 🔴 MAJOR (require major version bump)

**Working with Public Items:**

- ❌ Removing/renaming/moving any public items
- ❌ Adding a private struct field when all current fields are public
- ❌ Adding a public field when no private field exists

**Type and Representation Changes:**

- ❌ Changing alignment/layout/size of well-defined types
- ❌ Adding/removing `repr(packed)`, `repr(align)`, `repr(C)` for types with public fields
- ❌ Changing `repr(packed(N))` or `repr(align(N))` if it changes alignment/layout
- ❌ Removing `repr(<int>)` from enum
- ❌ Changing primitive representation of `repr(<int>)` enum
- ❌ Removing `repr(transparent)`
- ❌ Changing order of public fields in `repr(C)` types

**Enums:**

- ❌ Adding new enum variants (without `#[non_exhaustive]`)
- ❌ Adding new fields to enum variants

**Traits:**

- ❌ Adding non-defaulted trait item
- ❌ Any change to trait item signatures
- ❌ Adding trait item that makes trait non-object-safe
- ❌ Adding type parameter without default

**Generics:**

- ❌ Tightening generic bounds
- ❌ Generalizing type to use generics (with possibly different types)
- ❌ Capturing more generic parameters in RPIT

**Functions:**

- ❌ Adding/removing function parameters
- ❌ Generalizing function with type mismatch

**Attributes:**

- ❌ Switching from `no_std` support to requiring `std`
- ❌ Adding `#[non_exhaustive]` to existing enum/variant/struct with no private fields

**Cargo:**

- ❌ Removing a Cargo feature
- ❌ Removing feature from list if it changes functionality

### 🟢 MINOR (require minor version bump)

**Adding Items:**

- ✅ Adding new public items (functions, types, modules)
- ✅ Adding/removing private fields when at least one already exists
- ✅ Going from tuple struct with all private fields to normal struct, or vice versa

**Representation Changes:**

- ✅ Changing private fields in `repr(C)` types
- ✅ Adding variants to `repr(C)` enum with `#[non_exhaustive]`
- ✅ Adding `repr(C)` to default representation
- ✅ Adding `repr(<int>)` to enum
- ✅ Adding `repr(transparent)` to default representation

**Generics:**

- ✅ Loosening generic bounds
- ✅ Adding defaulted type parameters
- ✅ Generalizing type to use generics (with identical types)
- ✅ Changing generic type to more generic type
- ✅ Capturing fewer generic parameters in RPIT

**Functions:**

- ✅ Generalizing function to use generics (supporting original type)
- ✅ Making an `unsafe` function safe

**Cargo:**

- ✅ Adding new Cargo feature
- ✅ Changing dependency features (if no breaking changes)
- ✅ Adding dependencies

### ⚠️ POSSIBLY-BREAKING (depends on context)

- ⚠️ Adding defaulted trait item (may conflict with local traits)
- ⚠️ Adding inherent items (may conflict with trait methods)
- ⚠️ Introducing new function type parameter (rarely breaks code)
- ⚠️ Changing minimum Rust version required
- ⚠️ Changing platform and environment requirements
- ⚠️ Removing optional dependency (if it's in feature list)
- ⚠️ Introducing new lints (may break projects with `#![deny(warnings)]`)

## Mitigation Strategies for Breaking Changes

### For Item Removal

1. Mark items as `#[deprecated]`
2. For renames, use `pub use` for re-export
3. Optional: use feature flag for deprecation

### For Structs/Enums

1. Use `#[non_exhaustive]` from the start
2. Provide constructors instead of direct construction
3. Implement `Default` trait

### For Traits

1. Always provide default values for new items
2. Use sealed trait pattern to prevent external implementations
3. Introduce new items instead of changing existing ones

### For Functions

1. Create new functions with new signatures
2. Use builder pattern for functions with many parameters
3. Apply generics with default bounds

### For Features

1. Document all features explicitly
2. Don't include potentially breaking features in `default`
3. Use `dep:` syntax for optional dependencies

## Change Verification Checklist

### Before Release Always Check

**API Changes:**

- [ ] Removed/renamed public items? → MAJOR
- [ ] Changed public function signatures? → MAJOR
- [ ] Added fields to struct with public fields? → MAJOR
- [ ] Changed trait definitions? → check categories above
- [ ] Changed generic bounds? → check tightening/loosening

**Type Layout:**

- [ ] Changed `repr` attributes? → check table above
- [ ] Changed size/alignment of type with documented layout? → MAJOR

**Dependencies:**

- [ ] Removed features? → MAJOR
- [ ] Removed optional dependencies? → POSSIBLY-BREAKING
- [ ] Increased minimum Rust version? → POSSIBLY-BREAKING

**Documentation:**

- [ ] All public changes documented?
- [ ] CHANGELOG updated?
- [ ] Migration guide provided (for major changes)?

## Specifics for Different Situations

### no_std Libraries

- Switching from `no_std` to `std` → MAJOR
- Prefer feature flags: `std = []`

### Minimum Supported Rust Version (MSRV)

- Specify via `package.rust-version` in Cargo.toml
- MSRV update typically → MINOR (but check project policy)
- Document version support policy

### Cargo Features

- New feature → MINOR
- Removing feature → MAJOR
- Renaming → use alias or deprecation

### Lints

- New lints (deprecated, must_use) → MINOR
- May break projects with `#![deny(warnings)]`
- This is acceptable, but document it

## Quick Reference: Common Scenarios

| Change | Version | Note |
| ------ | ------- | ---- |
| Adding function | MINOR | Safe |
| Removing function | MAJOR | Use deprecation |
| Changing function parameters | MAJOR | Create new function |
| Adding trait method with default | MINOR | But may conflict |
| Changing trait method | MAJOR | Create new trait |
| Adding field to struct (all fields public) | MAJOR | Use `#[non_exhaustive]` |
| Adding field (has private fields) | MINOR | Safe |
| Adding enum variant without `non_exhaustive` | MAJOR | Use `#[non_exhaustive]` |
| Adding `#[must_use]` | MINOR | Lint, not breaking |
| Changing MSRV | MINOR* | *Per recommendations |
| Adding `repr(C)` | MINOR | To default repr |
| Removing `repr(C)` | MAJOR | If layout matters |

## Decision-Making Principles

1. **When in doubt, consider it MAJOR:** Better safe than sorry
2. **Document everything:** Especially "possibly-breaking" changes
3. **Use `#[non_exhaustive]`:** Provides future flexibility
4. **Test with cargo-semver-checks:** Automated verification
5. [**Follow API Guidelines:**](https://rust-lang.github.io/api-guidelines/)
6. **Communicate with users:** Especially for edge cases

## Verification Tools

- **cargo-semver-checks** — automatic SemVer compatibility checking
- **rust-semverver** — experimental verification tool
- **cargo-public-api** — track public API changes

## Useful Links

- [Cargo SemVer Reference](https://doc.rust-lang.org/cargo/reference/semver.html)
- [API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [SemVer Specification](https://semver.org/)

## Advanced Scenarios

### Object Safety Changes

- Making trait non-object-safe → MAJOR
- Adding associated const/static → breaks `dyn Trait`
- Making trait object-safe → MINOR (safe change)

### Repr Attribute Combinations

```rust
// MAJOR: Adding repr(packed) to any struct
#[repr(packed)]
pub struct Foo { pub a: u8, pub b: u32 }

// MINOR: Adding repr(C) to default repr
#[repr(C)]
pub struct Bar { pub x: i32 }

// MAJOR: Removing repr(transparent)
// was: #[repr(transparent)]
pub struct Wrapper<T>(T);
```

### Generic Parameter Capturing

```rust
// MAJOR: Capturing more lifetimes in RPIT
// Before: impl Iterator + use<'a>
// After:  impl Iterator + use<'a, 'b>

// MINOR: Capturing fewer lifetimes
// Before: impl Iterator + use<'a, 'b>
// After:  impl Iterator + use<'a>
```

### Sealed Traits Pattern

```rust
// Use this to prevent breaking changes from trait modifications
mod private {
    pub trait Sealed {}
}

pub trait MyTrait: private::Sealed {
    // Can safely add methods with defaults
    fn new_method(&self) {}
}

impl private::Sealed for MyType {}
impl MyTrait for MyType {}
```

## Common Pitfalls to Avoid

### ❌ Don't Do This (MAJOR Breaking Changes)

```rust
// Adding field to all-public struct
pub struct Config {
    pub timeout: u64,
    pub retries: u32,
    // Adding `pub max_size: usize` breaks construction
}

// Changing function signature
pub fn process(data: Vec<u8>) { }
// to: pub fn process(data: &[u8]) { } // BREAKS!

// Adding non-defaulted trait item
pub trait Handler {
    fn handle(&self);
    // Adding `fn validate(&self) -> bool;` BREAKS!
}
```

### ✅ Do This Instead (Safe Alternatives)

```rust
// Use non_exhaustive from the start
#[non_exhaustive]
pub struct Config {
    pub timeout: u64,
    pub retries: u32,
}

impl Config {
    pub fn new(timeout: u64, retries: u32) -> Self {
        Self { timeout, retries }
    }
}

// Create new function for signature changes
pub fn process_vec(data: Vec<u8>) { }
pub fn process(data: &[u8]) { }  // New function, safe!

// Always provide defaults for trait items
pub trait Handler {
    fn handle(&self);
    fn validate(&self) -> bool { true }  // Default provided
}
```

## Edition-Specific Considerations

### Rust 2024 RPIT Capturing

- All in-scope lifetimes captured by default
- Use `+ use<>` to capture fewer → breaking change
- Maximally compatible by default

### Closure Capture Changes

- repr(packed) affects closure captures
- Can cause compilation errors in user code
- Consider this when changing repr attributes

## Testing Strategy

### Before Major Release

1. Run `cargo-semver-checks` on public API
2. Test with downstream dependents
3. Check for common patterns that might break
4. Verify documentation completeness
5. Prepare migration guide

### Before Minor Release

1. Verify new items don't conflict commonly
2. Test feature combinations
3. Check MSRV compatibility if changed
4. Update changelog with all additions

### Continuous Integration

```yaml
# Example CI check
- name: Check SemVer
  run: |
    cargo install cargo-semver-checks
    cargo semver-checks check-release
```

## When Breaking Changes Are Necessary

Sometimes breaking changes are inevitable. When they are:

1. **Plan ahead:** Announce in advance
2. **Deprecation period:** Give users time to migrate
3. **Clear migration path:** Provide detailed guide
4. **Version clearly:** Use proper major version bump
5. **Consider branches:** Backport critical fixes to old major versions

### Communication Template

```markdown
## Breaking Changes in v2.0.0

### Removed: `old_function`

- **Reason:** Superseded by more efficient implementation
- **Migration:** Use `new_function` instead
- **Example:**

    ```rust
    // Before
    old_function(data);

    // After
    new_function(&data);
    ```
```

## Summary Flowchart

```plaintext
Is it a public API change?
├─ No → Consider PATCH or MINOR (docs, internal changes)
└─ Yes → Continue
    │
    Does it remove/rename/change existing public items?
    ├─ Yes → MAJOR
    └─ No → Continue
        │
        Does it add new requirements (trait items, bounds)?
        ├─ Yes → Check if defaulted
        │   ├─ Not defaulted → MAJOR
        │   └─ Defaulted → MINOR (possibly-breaking if conflicts)
        └─ No → Continue
            │
            Does it change type layout/size/alignment?
            ├─ Yes → Check if well-defined
            │   ├─ Well-defined → MAJOR
            │   └─ Not well-defined → MINOR
            └─ No → Likely MINOR
                │
                Document the change!
```
