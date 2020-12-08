import time
from TDStoreTools import StorageManager
from datetime import datetime as dt
import os
import shutil

TDF = op.TDModules.mod.TDFunctions

class ToxToolsExt:
	"""
	ToxToolsExt is the main extension for the package ToxTools
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

		self.Flash_duration 	= 4
		self.Defaultcolor		= self.ownerComp.pars('Defaultcolor*')
		self.DirtyCompsTable	= self.ownerComp.op('dirtyComps')
		self.SelectedCompsTable	= self.ownerComp.op('selectedComps')
		self.DirtyCompsDialog	= self.ownerComp.op('unsavedCompsDialog')
		self.Lister				= self.DirtyCompsDialog.op('lister')

		# adding attributes for a single manager setup with ToxTools, eventually need to check for other managers
		self._defaultManager = self.ownerComp.op('devToxManager')
		self._singleManager = True

	@property
	def configParser(self):
		return self.ownerComp.op('configParser')


	def GetTimestamp(self):
		#print(dt.now().isoformat())
		return dt.now().strftime('%Y_%m_%d__%H_%M_%S')

	def GetNetworkFolderPath(self, rootComp, targetComp, rootFolder = None, returnPathsOnly = False, includeTarget = False):
		parentOp = targetComp.parent()

		if rootFolder[-1] != '/':
			rootFolder = rootFolder + '/'

		if not os.path.exists(rootFolder):
			os.makedirs(rootFolder)
		
		# Create list of ops needed to construct directory paths
		opList = []
		opList.append(targetComp.name)
		if rootComp != targetComp:
			while parentOp != rootComp:
				opList.append(parentOp.name)
				parentOp = parentOp.parent()
		
		# Create dir paths by joining op names
		dirPathsList = []
		s = '/'
		for item in reversed(opList):
			newItem = s.join(reversed(opList))
			dirPathsList.append(newItem)
			opList.pop(0)
		
		# Append root folder to beginning of all list entries
		updatedPathsList = []
		for item in dirPathsList:
			item = rootFolder + item
			updatedPathsList.append(item)

		if returnPathsOnly:
			return updatedPathsList[0]

		# If includeTarget is false, remove that entry from the list to 
		# prevent folder from being made and return that target's parent
		if includeTarget == False:
			if len(updatedPathsList) > 1:
				updatedPathsList.pop(0)
			else:
				splitStr = updatedPathsList[0].split('/')
				if targetComp.name in splitStr:
					splitStr.remove(targetComp.name)
				updatedPathsList[0] = '/'.join(splitStr)
				
		# Create directories from updatedPathsList
		for path in reversed(updatedPathsList):
			if not os.path.exists(path):
				os.mkdir(path)

		return updatedPathsList[0]

	def SaveTox(self, comp, path, doBackup = False, backupInfo = {'date':True, 'suffix':None}, enableToeBackup=False):
		dtm = self.FindDevToxManager(comp)
		# debug('!!!!! ', path)
		# a shitty stop gap to stop from making a defaulted path format and filename
		formatSavePath = True
		if (path is not None) and (comp.par.externaltox.mode == ParMode.CONSTANT):
			saveLoc = path
			if comp != dtm.par.Rootcomp.eval():
				existingFilepath = path + '/' + comp.name + '.tox'
				toxName = comp.name
			else:
				#existingFilepath = path + '/root_' + comp.name + '.tox'
				# quick fix for now to make sure intent twitter project can be worked on
				# ignoring this altogether right now since we are using Tox Folders anyways.
				existingFilepath = path + '/' + comp.name + '.tox'
				toxName = comp.name
		elif (comp.par.externaltox.mode == ParMode.EXPRESSION) or (comp.par.externaltox.mode == ParMode.CONSTANT):
			# if no path is provided, use the comp's external tox parameter, and reset the exsiting file path to this as well
			saveLoc = comp.par.externaltox.eval()
			existingFilepath = saveLoc
			toxName = comp.name
			formatSavePath = False
		else:
			# no way to save bail
			return

		relPath = tdu.collapsePath(saveLoc)

		try:
			backedUpToxpath = None
			if os.path.isfile(existingFilepath):
				if doBackup == True:
					backedUpToxpath = self.BackupTox(existingFilepath, backupInfo)						
			
			# format our tox path or don't, if we're formatting it, we set its value
			if formatSavePath:
				savedToxpath = '{dir_path}/{tox}.tox'.format(dir_path = relPath, tox = toxName)
				comp.par.externaltox = savedToxpath
			else:
				savedToxpath = relPath

			# setup our module correctly
			if backedUpToxpath == None:
				comp.par.savebackup = enableToeBackup

			# set color for COMP
			comp.color = (0.0, 0.45, 0.68)

			# save our tox
			comp.save(savedToxpath)

			# flash color
			self.Flash_bg("Bgcolor")

			# create and print log message
			log_msg 		= "{} saved to {}/{}".format(comp, 
														project.folder, 
														savedToxpath)
			self.Logtotextport(log_msg)

			return {'savedTox':savedToxpath, 'backedUpTox':backedUpToxpath}

		except:
			import traceback; traceback.print_exc()

	
	def BackupTox(self, path, backupInfo = None):
		toxToMove = path
		toxFilename = os.path.split(path)[-1]
		backupLoc = os.path.split(path)[0]
		backupFolder = backupLoc + '/Backup'
	
		timestamp = self.GetTimestamp()

		if os.path.isdir(backupFolder) == False:
			os.mkdir(backupFolder)

		if backupInfo != None:
			date = backupInfo.get('date')
			suffix = backupInfo.get('suffix')
			if date == True:
				timestampedToxname = toxFilename[:-4] + '_' + timestamp + '.tox'
				movedTox = shutil.move(toxToMove, backupFolder + '/' + timestampedToxname)
				if suffix != None:
					suffixedToxname = movedTox[:-4] + '_' + suffix + '.tox'
					movedTox = shutil.move(movedTox, suffixedToxname)
			else:
				if suffix != None:
					 suffixedToxname = toxFilename[:-4] + '_' + suffix + '.tox'
					 movedTox = shutil.move(toxToMove, backupFolder + '/' + suffixedToxname)
		else:
			timestampedToxname = toxFilename[:-4] + '_' + timestamp + '.tox'
			movedTox = shutil.move(toxToMove, backupFolder + '/' + timestampedToxname)

		# debug('MOVEDTOX:', movedTox)
		return movedTox

	def UpdateVersion(self, comp):
		customPages = comp.customPages
		if 'Tox Version' not in customPages:
			versionPage = comp.appendCustomPage('Tox Version')
			newTuplet = versionPage.appendInt('Version')
			versionPar = newTuplet[0]
			versionPar.readOnly = True
			versionPar.val = 1
		else:
			comp.par.Version += 1

	
	def ExternalizeComp(self, comp, pathInfo = {'pathType':'choose', 'makeToxFolder':True}, backupInfo = {'date':True, 'suffix':None}, doVersion = True, enableToeBackup = False, relativeToxPath = True, updateToxPathPar = True):
		if doVersion:
			self.UpdateVersion(comp)

		# if backupInfo is None, don't save backup toxes
		doBackup = False
		if backupInfo is not None:
			doBackup = True

		if pathInfo != None:
			pathType = pathInfo.get('pathType')
			if pathType == 'choose':
				savePath = ui.chooseFolder(title="TOX Location", start=project.folder)
			elif pathType == 'simple':
				savePath = pathInfo.get('savePath')
			elif pathType == 'networkPath':
				rootComp = pathInfo.get('rootComp')
				rootFolder = pathInfo.get('rootFolder')

				parenthood = TDF.parentLevel(rootComp, comp)
				if parenthood != None:
					savePath = self.GetNetworkFolderPath(rootComp, comp, rootFolder)

			if pathInfo.get('makeToxFolder', False) == True:
				# Check whether toxfolder exists
				toxfolderPath = savePath + '/' + comp.name
				if os.path.isdir(toxfolderPath) == False:
					os.mkdir(toxfolderPath)
				savePath = toxfolderPath
			
			savedToxInfo = self.SaveTox(comp, savePath, doBackup=doBackup, backupInfo=backupInfo, enableToeBackup=enableToeBackup)
			savedTox = savedToxInfo['savedTox']
			if savedTox != None:
				if relativeToxPath:
					extToxParPath = tdu.collapsePath(savedTox)
					if extToxParPath != comp.par.externaltox.val:
						if updateToxPathPar:
							comp.par.externaltox = extToxParPath

				parentExternal = False
				if comp.parent().par.externaltox != '':
					parentExternal = True
				
			return {'savedTox':savedTox, 'externalToxPathPar':comp.par.externaltox.eval(), 'backedUpTox':savedToxInfo['backedUpTox'], 'parentExternal':parentExternal}

		else:
			#savePath = '/'.join(comp.par.externaltox.val.split('/')[:-1])
			savePath = None
			savedToxInfo = self.SaveTox(comp, savePath, doBackup=doBackup)

	def UnexternalizeComp(self, comp, tagToAppend=None):
		comp.par.externaltox = ''
		comp.color = (0.545, 0.545, 0.545)
		if tagToAppend != None:
			comp.tags.add(tagToAppend)

	def FindDevToxManager(self, comp):
		compToSave = comp
		manager = None
		if self._singleManager:
			defManager = self._defaultManager
			defManRoot = defManager.par.Rootcomp.eval()
			if (bool(TDF.parentLevel(defManRoot, comp)) or (defManRoot is comp)):
				manager = self._defaultManager
		else:
			devToxManagers = op('/').findChildren(tags = ['DevToxManager'])

			if len(devToxManagers) > 0:
				for dtm in devToxManagers:
					rootComp = dtm.par.Rootcomp.eval()
					parenthood = TDF.parentLevel(rootComp, compToSave)
					if parenthood != None:
						manager = dtm
						break
		
		return manager

	def GotSaveShortcut(self, comp):
		manager = self.FindDevToxManager(comp)
		if manager != None:
			if manager.par.Saveshortcut != False:
				manager.PromptForSave(comp)
		else:
			self.PromptNoSaveMessage(comp)

	def GotQuitShortcut(self):
		numDirtyComps = self.PromptUnsavedComps()
		if numDirtyComps == 0:
			project.quit()

	def GotShowUnsavedShortcut(self):
		numDirtyComps = self.PromptUnsavedComps()
		if numDirtyComps == 0:
			message = ui.messageBox('Warning', 'There are no dirty toxes', buttons=['OK'])

	def PromptUnsavedComps(self):
		self.DirtyCompsTable.clear(keepFirstRow=True)
		dirtyComps = self.GetDirtyComps() # list of lists, each entry is [name, path, owner manager path]
		allSaveNames = self.GetSaveNames()
		# if there are no save names we don't check against them
		checkSaveNames = bool(len(allSaveNames))
		# debug(allSaveNames, checkSaveNames)

		if len(dirtyComps) > 0:
			for c in dirtyComps:
				isSelected = 1
				if checkSaveNames:
					if c[0] in allSaveNames:
						isSelected = 1
					else:
						isSelected = 0
				self.DirtyCompsTable.appendRow(c[1:] + [isSelected])
			self.DirtyCompsDialog.par.Windowcomp.eval().par.winopen.pulse()
		
		return len(dirtyComps)
	
	def GetDirtyComps(self):
		root = op('/')
		devToxManagers = root.findChildren(tags = ['DevToxManager'])
		dirtyCompsList = []

		# for dtm in devToxManagers:
		# 	parenthood = TDF.parentLevel(op.ToxTools, dtm)
		# 	if parenthood != None:
		# 		devToxManagers.remove(dtm)

		if len(devToxManagers) > 0:
			for dtm in devToxManagers:
				dirtyComps = dtm.GetDirtyComps()
				for c in dirtyComps:
					dirtyCompsList.append(c)

		return dirtyCompsList

	def GetSaveNames(self):
		'''
		gets name scopes from any managers and compiles a set
		'''
		allSaveNames = set([])
		root = op('/')
		devToxManagers = root.findChildren(tags = ['DevToxManager'])
		dirtyCompsList = []
		if len(devToxManagers) > 0:
			for dtm in devToxManagers:
				dtmSaveNameSet = dtm.GetSaveNames()
				for name in dtmSaveNameSet:
					allSaveNames.add(name)
		
		return allSaveNames


	def QuitProject(self):
		confirmation = ui.messageBox('Confirmation', "Are you sure you'd like to quit?\nAny unsaved external Comps will not be saved!", buttons=['Quit', 'Cancel'])

		if confirmation == 0:
			project.quit()

	def SelectAllUnsavedComps(self):
		if self.DirtyCompsTable.numRows > 0:
			for item in self.DirtyCompsTable.rows()[1:]:
				item[2].val = 1

	def DeselectAllUnsavedComps(self):
		if self.DirtyCompsTable.numRows > 0:
			for item in self.DirtyCompsTable.rows()[1:]:
				item[2].val = 0

	def SaveSelected(self):
		if self.SelectedCompsTable.numRows > 0:
			for item in self.SelectedCompsTable.rows():
				compToSave = op(item[0].val)
				#savePath = '/'.join(compToSave.par.externaltox.val.split('/')[:-1])

				# getting save version setting from manager to make sure versions don't get added
				# on a bulk save
				manager = op(item[1].val)
				manager.DtmExternalizeComp(compToSave)
				#doVersion = manager.par.Updateversions.eval()
				#self.ExternalizeComp(compToSave, pathInfo=None, doVersion = doVersion)
				self.DirtyCompsDialog.par.Windowcomp.eval().par.winclose.pulse()
			self.PromptUnsavedComps()

	def SaveSelectedAndQuit(self):
		if 0 < self.SelectedCompsTable.numRows < self.DirtyCompsTable.numRows-1:
			confirmation = ui.messageBox('Confirmation', "Are you sure you'd like to save and quit?\nYou will lose any unsaved work!", buttons=['Continue', 'Cancel'])

			if confirmation == 0:
				self.SaveSelected()
				project.quit()
		elif self.SelectedCompsTable.numRows == 0:
			popup = ui.messageBox('Unable to complete request', 'Please select at least one comp to save and quit!', buttons=['OK'])
		else:
			self.SaveSelected()
			project.quit()

	def PromptNoSaveMessage(self, comp):
		title = "Warning"
		text = comp.path + " is not set to externalize"
		btns = ['OK']

		ui.messageBox(title, text, buttons=btns)

	def LoadSettings(self):
		#debug('Load settings!')
		self.configParser.LoadConfig()

	def SaveSettings(self):
		#debug('Save settings!')
		self.configParser.SaveConfig()

	def Flash_bg(self, parColors):
		'''
			Used to flash the background of the TD network. 

			Notes
			---------
			This is a simple tool to flash indicator colors in the
			background to help you have some visual confirmation that
			you have in fact externalized a file.

			Args
			---------
			parColors (str):
			> this is the string name to match against the parent's pars()
			> for to pull colors to use for changing the background
					
			Returns
			---------
			none		
		'''
		par_color 			= '{}*'.format(parColors)
		over_ride_color 	= parent().pars(par_color)

		# change background color (0.1, 0.105, 0.12)
		ui.colors['worksheet.bg'] 	= over_ride_color
		delay_script 				= "ui.colors['worksheet.bg'] = args[0]"
		
		# want to change the background color back
		run(delay_script, self.Defaultcolor, delayFrames = self.Flash_duration)		

		return


	def Logtotextport(self, logMsg):

		if self.ownerComp.par.Logtotextport:
			print(logMsg)

		else:
			pass

		return	

	def OpenUiPanel(self):
		uiPanel = self.ownerComp.op('configUi')
		uiPanel.openViewer()



### Par Executes ###

	def Loadconfig(self, par):
		self.LoadSettings()

	def Saveconfig(self, par):
		self.SaveSettings()

	def Uipanel(self, par):
		self.OpenUiPanel()

	def Managerpars(self, par):
		self.ownerComp.op('devToxManager').openParameters()


### functions to be eventually turned into a parent package class or external module ###

	def UpgradeComp(self, comp):
		'''
		bespoke package comp upgrade based on Peter's project template
		This is meant to be called by the tdPackageManager instead of the
		default upgrade functionality, it has no check for correct component
		setup, so should only be called by the packageManager modified by peter,
		which has alredy done the right checks
		'''
		#compSource = self.GetCompSource(comp)

		if '!pkgCompClass' in comp.tags:
		
			self.UpgradeCompPars(comp)
			self.UpgradeCompVersion(comp)
			self.UpgradeSysLocal(comp)
		
		elif '!pkgCompClone' in comp.tags:
			comp.par.enablecloningpulse.pulse()
			self.UpgradeCompVersion(comp)

	def UpdateComp(self, comp):
		'''
		custom Update to be called by packageMangager onPreUpdate()
		this mostly just syncs the version of all collection sourceComps
		with the package's version for exporting
		'''
		if hasattr(comp.par, 'Pkgversion'):
			comp.par.Pkgversion.val = self.ownerComp.par.Pkgversion.val
		return

	def GetCompSource(self, comp):
		pkgComps = comp.par.Pkgpackage.eval().par.Pkgcomponents.eval()
		compSource = pkgComps.op(comp.par.Pkgsource.eval())
		return compSource

	def UpgradeCompPars(self, comp, destroyOthers = True):
		'''
		updates the parameters on a parent by comparing with the template
		'''
		template = self.GetCompSource(comp)
		tempPars = TDJ.opToJSONOp(template)
		TDJ.addParametersFromJSONOp(comp, tempPars, replace=True, setValues=False, destroyOthers = destroyOthers)
		
		cmd = "op('"+comp.path+"').par.reinitextensions.pulse()"
		run(cmd, delayFrames = 1, delayRef = op.TDResources)

	def UpgradeCompVersion(self, comp):
		template = self.GetCompSource(comp)
		verPar = comp.par.Pkgversion
		verPar.val = template.par.Pkgversion.val

	def UpgradeSysLocal(self, comp):
		if comp.op('sysLocal'):
			comp.op('sysLocal').par.enablecloningpulse.pulse()