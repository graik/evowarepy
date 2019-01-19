##  evoware/py -- python modules for Evoware scripting
##   Copyright 2014 - 2019 Raik Gruenberg
##
##   Licensed under the Apache License, Version 2.0 (the "License");
##   you may not use this file except in compliance with the License.
##   You may obtain a copy of the License at
##
##       http://www.apache.org/licenses/LICENSE-2.0
##
##   Unless required by applicable law or agreed to in writing, software
##   distributed under the License is distributed on an "AS IS" BASIS,
##   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##   See the License for the specific language governing permissions and
##   limitations under the License.

from . import fileutil as F
import os.path as osp
import os
import logging, logging.handlers

class EvoTask(object):
    """
    Basic folder and log handling for Evo workflow tasks.
    
    EvoTask.f_project: 
    
        The task is supposed to read and write from a sub-folder within a
        workflow "project folder". This project folder must be already
        existing.
    
    EvoTask.f_task:
    
        The sub-folder is typically composed from:

            EvoTask.f_task = project folder + EvoTask.F_SUBFOLDER

        This folder will be created if it doesn't already exist. The default
        F_SUBFOLDER name should be overridden by derrived classes. It can
        also be changed for a given instance through the constructor
        (taskfolder='<other_name>'). Moreover, it is also possible to create
        a EvoTask instance with a fully qualified, already existing,
        taskfolder which, in this case, could also be located outside the
        project folder.
    
    Typical usage:
    >>> task = EvoTask('data/mynewproject')
    
    This will create a new sub-folder 'evotask' within data/mynewproject or
    use the already existing sub-folder. It will create a new log file task.log
    within this sub-folder (rotating away previous logs)
    """
    
    #: default task-specific sub-folder name for input and output. Override!
    F_SUBFOLDER = 'evotask'
    #: default task-specific log file name
    F_LOG = 'task.log'
    
    def __init__(self, projectfolder='.', taskfolder=None, logfile=None,
                 loglevel=logging.INFO):
        """
        @param projectfolder - str, parent folder for Evo Task subfolder ['.']
        @param taskfolder - str, input/output folder for task [create new]
                            Defaults to self.F_SUBFOLDER class variable.
        @param logfile - str, file name for logfile; will be created as rotating
                         log in task folder unless a full path is given [F_LOG]
        """
        logging.info('Initiating new task: %s in %s', self.__class__.__name__,
                      projectfolder)
        
        self.f_project = F.absfile(projectfolder)
        if not osp.isdir(self.f_project):
            logging.error('Project folder %s not found.' % self.f_project)
            raise IOError('Project folder %s not found.' % self.f_project)
        
        self.f_task = self.prepareFolder()
        
        logfile = logfile or self.F_LOG
        if not osp.isabs(logfile):
            logfile = osp.join(self.f_task, logfile)
        
        self.log = logging.getLogger('evo.' + self.__class__.__name__)
        self.log.setLevel(loglevel)

        hdlr = logging.handlers.RotatingFileHandler(logfile,backupCount=5)
        self.log.addHandler(hdlr)
        self.log.propagate = False  ## don't copy to root log
        
        self.log.info('Task %s initiated in %s' % (self.__class__.__name__ , 
                                              self.f_task) )

    
    def prepareFolder( self, taskfolder=None ):
        """
        Create needed output folders if not there.
        @return str, full path to (if needed created) existing folder for task
        """
        taskfolder = taskfolder or self.F_SUBFOLDER

        ## given task folder is full path and exists as directory
        if osp.isdir(taskfolder):
            return taskfolder
        
        r = osp.join(self.f_project, taskfolder)
        logging.info('Task folder is set to ' + r)
        
        if not osp.isdir(r):
            logging.info('Creating new folder ' + r)
            os.mkdir(r)
        
        if not osp.isdir(r):
            msg = 'Could not create task folder %r.' % r
            logging.error(msg)
            raise IOError(msg)
        
        return r


######################
### Module testing ###
import testing, tempfile

class Test(testing.AutoTest):
    """Test Worklist"""

    TAGS = [ testing.NORMAL ]
    DEBUG = False

    def prepare( self ):
        self.f_project = tempfile.mkdtemp(prefix='test_evotask_')
        self.loglevel = logging.WARNING
        if self.local:
            self.loglevel = logging.INFO
        
        logging.basicConfig(level=self.loglevel)
    
    def cleanUp(self):
        if not self.DEBUG:
            F.tryRemove(self.f_project, tree=True)
    
    def test_evotask_default(self):
        t = EvoTask(projectfolder=self.f_project)
        
        self.assertTrue(osp.exists(t.f_task), 'no task folder')
        self.assertTrue(osp.exists(osp.join(t.f_task, t.F_LOG)), 'no log file')

if __name__ == '__main__':
    
    testing.localTest(debug=False)
