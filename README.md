evoware
=======

python package supporting / simplifying the creation of Tecan Evoware scripts

Limitations
-----------

evowarepy is using `xlrd` for reading and writing Excel files. Unfortunately, xlrd only works with the older **.xls** format (Previous versions of the package were also reading xlsx but this was error-prone and more recent versions of xlrd reject xlsx files.)

Requirements
------------
Since all this is yet a bit experimental, setup has not been streamlined yet. Here is what we need at the end:

  * Python (3.x)
  * Python TkInter extension (needed for showing file open and warning / info dialogs)
  * python packages numpy, xlrd
  * `evoware` python package folder (found within the evowarepy project directory)
    * this folder has to be added to the PYTHONPATH system or user variable
  * `evoware/scripts` folder with end-user programs (also found within evowarepy project directory)

The python scripts in evoware/scripts can then be executed from regular Tecan Evoware scripts. They will read in Excel files as needed and create pipetting worklist files. These worklist files are then executed using the standard Evoware instruction. 

Installation based on win-bash:
--------------------------------

1. download and install Python 3.11 for Windows
     * ensure the TK/TKinter checkbox is checked
3. download and install Git commandline (and GUI) for Windows: https://git-scm.com
4. download Win-bash from https://sourceforge.net/projects/win-bash/files/shell-complete/latest/
     * extract to new folder in `C:\Program Files`
     * optional: add this folder to PATH using  START / Computer / System Properties / Advanced System Settings
     * create a link to the `bash.exe` in Start menu
5. Fetch and install evoware package through Win-bash terminal:
     *  `cd /Users/labuser/`  ## move into your user folder or any alternative location
     *  `mkdir py; cd py` ## create a folder for the python source code
     *  `git clone https://github.com/graik/evowarepy.git`
     *  `pip install ./evowarepy` 
6. Test the installation:
     * `cd py/evowarepy/evoware`
     * `python testing.py -e OLD`
       * Note: this will bring up a couple of dialog boxes, including fake error messages... that's OK, it's part of the testing


Development setup on OSX
-------------------------

  * `brew install python python-tk`
  * `git clone https://github.com/graik/evowarepy.git`
    * will create a `evowarepy` folder in your current directory
  * `pip install -e evowarepy`
    * installs python dependencies (from requirements.txt and then **links** the evoware package into the python site-packages folder)

Test the python package as shown above
