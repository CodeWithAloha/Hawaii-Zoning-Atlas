# Contributing

## Request for changes / Pull Requests

To start create a fork of the [Hawaii-Zoning-Atlas](https://github.com/CodeWithAloha/Hawaii-Zoning-Atlas) repo to commit your changes to. Methods to fork a repository can be found in the [GitHub Documentation](https://docs.github.com/en/get-started/quickstart/fork-a-repo).

Then add your fork as a local project:

```sh
# Using HTTPS
git clone https://github.com/CodeWithAloha/Hawaii-Zoning-Atlas

# Using SSH
git clone git@github.com:CodeWithAloha/Hawaii-Zoning-Atlas.git
```

> [Which remote URL should be used ?](https://docs.github.com/en/get-started/getting-started-with-git/about-remote-repositories)

Then, go to your local folder

```sh
cd Hawaii-Zoning-Atlas
```

Add git remote controls :

```sh
# Using HTTPS
git remote add fork https://github.com/YOUR-USERNAME/Hawaii-Zoning-Atlas.git
git remote add upstream https://github.com/CodeWithAloha/Hawaii-Zoning-Atlas.git


# Using SSH
git remote add fork git@github.com:YOUR-USERNAME/Hawaii-Zoning-Atlas.git
git remote add upstream git@github.com/CodeWithAloha/Hawaii-Zoning-Atlas.git
```

You can now verify that you have your two git remotes:

```sh
git remote -v
```

## Receive remote updates

In view of staying up to date with the central repository :

```sh
git pull upstream main
```

## Choose a base branch

Before starting development, you need to know which branch to base your modifications/additions on. When in doubt, use main

| Type of change    |  |                Branches |
| :---------------- | :-: | ----------------------: |
| Documentation     |  |                `main` |
| Bug fixes         |  |                `main` |
| New features      |  |                `main` |
| New issues models |  | `YOUR-USERNAME/patch` |

```sh
# Switch to the desired branch
git switch main

# Pull down any upstream changes
git pull

# Create a new branch to work on
git switch --create patch/1234-name-issue
```

Commit your changes, then push the branch to your fork with `git push -u fork` and open a pull request on [the Hawaii-Zoning-Atlas](https://github.com/CodeforHawaii/Hawaii-Zoning-Atlas/) following the template provided.
