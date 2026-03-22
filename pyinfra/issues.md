# Migration Issues: Ansible to Pyinfra

## Goal

Migrate the original Ansible roles (starting with `basic_utils` and eventually all others) to a clean, modular Pyinfra implementation.  
Add a robust configuration system with hierarchical defaults, CI‑compatible variables, and per‑machine overrides.  
Create reusable Pyinfra operation collections (similar to `pyinfra-docker`) and shared utilities.  
Set up linting/formatting with Ruff, CI scripts, and documentation for contributors.

## Current Status

### Discoveries

- The original Ansible repository (branch `devel`) contains many roles besides `basic_utils` (e.g., `alacritty`, `docker`, `git-tools`, `zsh`, etc.).  
- `ci-inventory.yaml` defines a large set of enable flags and nested configuration objects (e.g., `basic_utils.enable_direnv`, `basic_utils.ssh_key`, `basic_utils.sdkman`, `basic_utils.gcr_ssh_agent`, etc.).  
- Templates exist for SSH config, Dart/Flutter proxy scripts, and many role‑specific files.  
- The current Pyinfra project already implements most of `basic_utils` features, plus new ones (SSH config paths, Python venvs, proxy scripts).  
- Ruff has been integrated and all code now passes linting/formatting.  
- Tests cover the core tasks, including the newly added Python and proxy features.  
- The repository structure now includes `basic_utils/tasks/`, `basic_utils/group_data/`, `basic_utils/inventory/`, and a `templates/` folder for proxy scripts.  
- Pyinfra has a robust built-in configuration system that we should leverage instead of building a custom one.

## New Deployment System

The main deployment system in `deploy.py` has been significantly enhanced to actually provision machines rather than just printing configuration. Key improvements include:

- **Collection Enable/Disable System**: Collections can now be dynamically enabled or disabled through configuration
- **Configuration Mapping**: Proper mapping between configuration flags and collection execution
- **Error Handling**: Robust error handling for missing or invalid configurations
- **Modular Architecture**: Each collection can be independently managed and tested

The deployment system now respects the hierarchical configuration (environment > machine > CI > global) and properly integrates with Pyinfra's native configuration system. This allows for flexible deployment scenarios where specific collections can be enabled or disabled based on the target environment or machine requirements.

### Phase 2: Remove unnecessary things

- Remove superfluous comments. The code should be clear without comments.
- Remove the unnecessary config parsing and its tests. (The _parse_bool that are lying around)
- Fix upper and lower casing of config values

### Phase 3: Role Migration
#### 3.1 Core Infrastructure
- [x] `basic_utils` role (mostly complete)
  - [ ] Final review and optimization
  - **Review Required**: Code and architecture review
  - **Testing Required**: Full integration test on actual machine

#### 3.2 Development Tools
- [ ] `git-tools` role migration
  - **Review Required**: Tool selection and configuration review
  - **Testing Required**: Test all git tools functionality

#### 3.3 Runtime Environments
- [ ] `sdkman` role migration (part of basic_utils)
  - [ ] Extract to separate role if needed
  - **Review Required**: SDK management approach review
  - **Testing Required**: Test SDK installation and switching
- [ ] ` languages` roles (Python, Node, Go, etc.)
  - **Review Required**: Version management strategy review
  - **Testing Required**: Test each language installation and tools

#### 3.4 Applications

### Phase 4: Integration and CI
- [ ] Create comprehensive test suite
  - [ ] Unit tests for all collections
  - [ ] Integration tests for common scenarios
  - [ ] End-to-end tests on clean machines
  - **Review Required**: Test coverage analysis
  - **Testing Required**: All tests must pass in CI
- [ ] Set up CI pipeline
  - [ ] GitHub Actions workflow for linting (Ruff)
  - [ ] GitHub Actions workflow for testing
  - [ ] GitHub Actions workflow for deployment
  - **Review Required**: CI pipeline design review
  - **Testing Required**: Test CI pipeline with PRs and merges
- [ ] Update documentation
  - [ ] Complete README with migration status
  - [ ] Collection-specific documentation
  - [ ] Contribution guidelines
  - **Review Required**: Documentation accuracy review
  - **Testing Required**: Test installation and setup following docs

### Phase 5: Optimization and Stability
- [ ] Performance optimization
  - [ ] Parallel execution where possible
  - [ ] Idempotency improvements
  - [ ] Error handling and recovery
  - **Review Required**: Performance benchmarks review
  - **Testing Required**: Performance tests on various configurations
- [ ] Security audit
  - [ ] Review all downloaded binaries and sources
  - [ ] Check for hardcoded secrets
  - [ ] Verify secure handling of credentials
  - **Review Required**: Security review meeting
  - **Testing Required**: Security scanning in CI
- [ ] Final migration validation
  - [ ] Feature parity checklist
  - [ ] End-to-end testing on original target machines
  - **Review Required**: Final sign-off from stakeholders
  - **Testing Required**: Complete regression test suite

## Process Requirements

### Review Process
1. **Every step marked "Review Required" must be:**  
   - Reviewed by the review agent after code completion
   - Address all feedback from the review
   - Re-review after changes until approved
2. **Review checkpoints:**
   - Architecture decisions
   - Major refactoring
   - New collection implementations
   - Final integration

### Testing Requirements
1. **Every step marked "Testing Required" must include:**
   - Unit tests for individual components
   - Integration tests for combined functionality
   - End-to-end tests where applicable
   - Documentation of test coverage
2. **Test validation:**
   - All tests must pass locally
   - All tests must pass in CI
   - No degradation in performance
   - No regression in existing functionality

### Project Structure Note
The entire project structure should be moved up from the current `basic_utils/` directory, since `basic_utils` is just one part of the overall provisioning system. The final structure should look like:

```
provision-machines/
├── pyinfra_collections/
│   ├── basic_utils/
│   ├── development_tools/
│   ├── runtime_environments/
│   └── applications/
├── config/
│   ├── global.py
│   ├── ci.py
│   └── machines/
├── group_data/
├── inventory/
├── shared/
│   ├── operations/
│   └── utilities/
├── tests/
├── ci/
├── docs/
└── scripts/
```

## Additional Considerations

- **Backward Compatibility**: Ensure the migration doesn't break existing setups
- **Configuration Migration**: Provide tools to migrate existing Ansible configurations
- **Documentation**: Keep documentation synced with each implementation step
- **Deprecation**: Clearly mark deprecated features with migration paths
- **Community**: Consider how contributions will be handled in the new structure