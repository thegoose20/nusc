# nusc
Project funded by The National Archives' Research and Innovation Grant with Newcastle University Special Collections

***
#### Table of Contents

[Project Overview](#project-overview)

[Data](#data)

[Setup and Usage](#setup-and-usage)

[Related Resources](#related-resources)

***

## Project Overview
Newcastle University Special Collections (NUSC) has been engaged in efforts to mitigate bias in its catalogues and curative practices through ‘Special for Everyone’, a project launched in 2020. This project sought to apply machine learning models developed for identifying gender biased language for the archives sector, specifically text classifiers trained on descriptive metadata from the University of Edinburgh's archival catalog ([Havens et al., 2025](https://doi.org/10.1145/3706598.3713217)).  Experiments with the models coupled with manual reviews indicated that NUSC's descriptive metadata didn't have much gender biased language, so in the second phase of the project, broader computational analytics were performed to investigate differences between the language of Edinburgh and Newcastle's descriptive metadata.

## Data
The primary data source for this repo is from the catalogs of [Newcastle University Special Collections & Archives](https://specialcollections.ncl.ac.uk).  EAD XML records were extracted in May 2025, with the analysis focusing on the descriptive metadata from four fields: *Title*, *Biographical / Historical*, *Scope and Contents*, and *Processing Information*.  Additionally, transcriptions of the Gertrude Bell Archive's material were extracted (also XML but not in EAD).  Analysis of the Bell descriptive metadata focused on three fields: *Title*, *Description*, and *Extent and Medium*.

The University of Edinburgh data used in this repo is from the catalog of the [University of Edinburgh Archive and Manuscript Collections](https://archives.collections.ed.ac.uk).  EAD XML records were extracted in May 2025, focusing on the descriptions in four metadata fields: *Title*, *Biographical / Historical*, *Scope and Contents*, and *Processing Information*.


## Setup and Usage

**Step 1:** Using your command line, navigate to the directory in which you'd like to place the repo and then clone the repo.

*If you're not familiar with command line tools, check out [this Bash tutorial](https://programminghistorian.org/en/lessons/intro-to-bash) (for Mac and Linux) or [this PowerShell tutorial](https://programminghistorian.org/en/lessons/intro-to-powershell) (for Windows) from the Programming Historian.*

```
git clone https://github.com/thegoose20/nusc.git
```

**Step 2:** Navigate into the repo.

```
cd nusc
```

**Step 3:** Create a virtual environment from the environment file provided in the repo.

```
conda env create -f environment.yml
```

**Step 4:** Activate your newly created virtual environment.
```
conda activate nusc
```

**Step 5:** Initialize the git repository.  

*If you're not familiar with git or GitHub, checkout GitHub's [Quick Start](https://docs.github.com/en/get-started/start-your-journey) and [Using Git](https://docs.github.com/en/get-started/using-git) documentation.*
```
git init
```

Now you're ready to begin running the Jupyter Notebooks (.ibynb files) in this repo!  The numbers at the start of each Notebook's name indicate the order in which they are intended to be run.

When you're done, shut down your virtual environment by entering the following in the command line:
```
conda deactivate
```
Re-activate the environment by running the command in step 4.


## Related Resources
* [gender-bias](https://github.com/thegoose20/gender-bias) - *repo with code training, developing, and testing the machine learning models*
* Lucy Havens, Benjamin Bach, Melissa Terras, and Beatrice Alex. 2025. Investigating the Capabilities and Limitations of Machine Learning for Identifying Bias in English Language Data with Information and Heritage Professionals. In *Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems (CHI '25).* Association for Computing Machinery, New York, NY, USA, Article 573, 1–22. [https://doi.org/10.1145/3706598.3713217](https://doi.org/10.1145/3706598.3713217)