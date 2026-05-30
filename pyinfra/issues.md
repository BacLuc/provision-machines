# Port all ansible roles to pyinfra

First read pyinfra/AGENTS.md and README.md.
Then continue porting all ansible roles to pyinfra.
Leave github_release_binary alone, this is good enough for now.
All configuration must be in [group_data](group_data).
Do the refine, plan, build, test, review cycle for each role.

The previous agent duplicated roles and did not respect the
auto injection mechanism of deploys via [include_children.py](operations/include_children.py)

In commit d07cff7e6c98afe9205185e262873ad6d34fe516 you have how the whole thing should be set up.
in [roles](../roles) you have the ansible roles.
You are in a devcontainer, you can run any command and should not stop until you tested
the roles thoroughly by running them all together.
Do not leave additional scripts or markdown files, i want a clean repository with working deploys.
