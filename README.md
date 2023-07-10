evoware
=======

python package supporting / simplifying the creation of Tecan Evoware scripts

Limitations
-----------

evowarepy is using `xlrd` for reading and writing Excel files. xlrd only works with the older **.xls** format. 

Manual Setup
------------

*Requirements:*
  * Python (3.x)
  * Python TkInter extension
  * python packages numpy, xlrd

*Install Python using homebrew:*
  * `brew install python python-tk`

*Download and setup evoware code*
  * `git clone https://github.com/graik/evowarepy.git`
    * will create a `evowarepy` folder in your current directory
  * `pip install -e evowarepy`
    * installs python dependencies (from requirements.txt and then links the evoware package into the python site-packages folder)

*Test the python package*
  * `cd evowarepy`
  * `cd evoware`
  * `python testing.py -e OLD`
    * this will run a test suite excluding tests labelled as OLD
      
Note: 

  This method will not actually move the evoware python package into the python packages folder but instead creates a link to its current   location. This allows you to change the code moving forward. Alternatively, `pip install eveowarepy` will move the python package into    the site-wide package folder. You can then remove the original evowarepy folder. Any changes to the original evowarepy project will then have to be applied through another pip install call.  

