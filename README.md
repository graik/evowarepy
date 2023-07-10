evoware
=======

python package supporting / simplifying the creation of Tecan Evoware scripts

Limitations
-----------

evowarepy is using `xlrd` for reading and writing Excel files. Unfortunately, xlrd only works with the older **.xls** format (Previous versions of the package were also reading xlsx but this was error-prone and more recent versions of xlrd reject xlsx files.)

Manual Setup
------------

Since all this is yet a bit experimental, setup has not been streamlined yet. Here is what we need at the end:

*Requirements:*
  * Python (3.x)
  * Python TkInter extension (needed for showing file open and warning / info dialogs)
  * python packages numpy, xlrd
  * `evoware` python package folder (found within the evowarepy project directory)
    * this folder has to be added to the PYTHONPATH system or user variable
  * `evoware/scripts` folder with end-user programs (also found within evowarepy project directory)

The python scripts in evoware/scripts can then be executed from regular Tecan Evoware scripts. They will read in Excel files as needed and create pipetting worklist files. These worklist files are then executed using the standard Evoware instruction. 

*Low-tech but a little tedious strategy:*

1. Download and install Python 3.11 for Windows
2. Create a folder `py` and a folder `pyscripts` in your local user directory or elsewhere, e.g. in `C:\Users\robotadmin\`
3. Download the current evowarepy code base as a zip file:
   * https://github.com/graik/evowarepy/archive/refs/heads/master.zip
   * (in case the link doesn't work: from github repo, look for the green "Code" button and there for the zip file option)
4. Unpack this zipfile into a temporary location
5. Move the `evoware` subfolder of `evowarepy` into `C:\Users\robotadmin\py\`
6. Move the **content** of the `scripts` subfolder into `C:\Users\robotadmin\pyscripts\`
7. Install python dependencies:
   * open Windows CMD terminal: (Start - type CMD)
   * `pip install xlrd numpy`
8. Add evoware to PYTHONPATH environment variable:
   * START / Computer / System Properties / Advanced System Settings
   * look for PYTHONPATH and add `C:\Users\robotadmin\py\` or whereever evoware was moved
9. Test your installation:
   * Run Windows CMD terminal (START - CMD)
   * `cd Users/robotadmin/py/evoware` (change according to your user directory)
   * `python testing.py -e OLD`

*Slightly more flexible strategy*

based on a linux bash terminal with git support which will allow us to quickly update the evowarepy code on the fly as the project progresses:

1. download and install Python 3.11 for Windows
2. download and install Git commandline and GUI for Windows: https://git-scm.com
3. download Win-bash from https://sourceforge.net/projects/win-bash/files/shell-complete/latest/
     * extract to new folder in `C:\Program Files`
     * optional: add this folder to PATH using  START / Computer / System Properties / Advanced System Settings
4. Fetch and install evoware package through Win-bash terminal:
     *  `cd`
     *  `git clone https://github.com/graik/evowarepy.git`
     *  `pip install evowarepy`
5. Test the installation:
     * `cd evowarepy/evoware`
     * `python testing.py -e OLD`


Development setup on OSX
-------------------------

  * `brew install python python-tk`
  * `git clone https://github.com/graik/evowarepy.git`
    * will create a `evowarepy` folder in your current directory
  * `pip install -e evowarepy`
    * installs python dependencies (from requirements.txt and then **links** the evoware package into the python site-packages folder)

Test the python package as shown above
