from TDStoreTools import StorageManager
TDF = op.TDModules.mod.TDFunctions

class DevToxManagerExt:
	"""
	DevToxManagerExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	@property
	def OnlySaveRoot(self):
		return self.ownerComp.par.Onlysaveroot.eval()

	def PromptForSave(self, compToSave):
		alwaysIgnoreTags = tdu.split(self.ownerComp.par.Alwaysignoretags.eval(), True)
		proceedWithSave = True
		proceedWithRootSave = False

		# if only save root comp is on, then check for what to do
		if self.OnlySaveRoot:
			# first check if the orginal compToSave was externalized and warn the user
			rootSaveOption = self.RootOnlyCheck(op(compToSave))
			if rootSaveOption == 0:
				proceedWithRootSave = True
				proceedWithSave = False
			if rootSaveOption == 1:
				proceedWithSave = True
			if rootSaveOption == 2:
				proceedWithRootSave = True
				proceedWithSave = True
			if rootSaveOption == 3:
				proceedWithRootSave = False
				proceedWithSave = False
		
		# Check whether compToSave has an "Ignore" tag
		if bool(set(compToSave.tags).intersection(alwaysIgnoreTags)) != False:
			proceedWithSave = False

		# Check if the comp is the root
		if compToSave == '/':
			proceedWithSave = False

		if proceedWithSave:
			self.DtmExternalizeComp(compToSave)

		if proceedWithRootSave:
			self.DtmExternalizeComp(self.ownerComp.par.Rootcomp.eval())

	def RootOnlyCheck(self, origComp):
		option = 0
		print(origComp.path)
		if origComp.path != self.ownerComp.par.Rootcomp.eval().path:
			if origComp.par.externaltox.eval() is not '':
				msgBoxTitle = "Comp is external!"
				msgBoxMsg = "This COMP (" + origComp.name + ") is external but you are set to save only the root.\n\nHow would you like to proceed?"
				msgBoxBtns = ["Save Root", "Save This Comp", "Save Both", "Cancel"]
				option =  ui.messageBox(msgBoxTitle, msgBoxMsg, buttons = msgBoxBtns)
		return option



	def DtmExternalizeComp(self, comp):
		# Default vars/args and values
		pathInfo = {'pathType':'simple'}
		makeToxFolder = True
		saveBackups = self.ownerComp.par.Savebackups.val
		updateVersions = self.ownerComp.par.Updateversions.val
		enableToeBackup = self.ownerComp.par.Enabletoebackup.val
		backupInfo = self.GetBackupInfo()

		newlyExternalized = False
		if comp.par.externaltox == '':
			newlyExternalized = True

		saveMsgBoxTitle = "Externalize COMP"
		saveMsgBoxMsg = "This COMP (" + comp.name + ") is not yet externalized.\n\nHow would you like to externalize this TOX?"
		saveMsgBoxBtns = ["Cancel", "Select Folder", "Use Network Path", "Edit Network Path Settings"]

		makeToxFolderTitle = "Make Tox Folder"
		makeToxFolderMsg = "Would you like to save this\ntox into a named folder?"
		makeToxFolderBtns = ["No", "Yes"]

		saveParentTitle = "Save Parent TOX"
		saveParentMsg = "This COMP (" + comp.name + ") has just been externalized!\n\nWould you also like to save its parent TOX?"
		saveParentBtns = ["No", "Yes"]

		# Check if comp is not external
		if comp.par.externaltox == '':
			confirmation = ui.messageBox(saveMsgBoxTitle, saveMsgBoxMsg, buttons = saveMsgBoxBtns)

			# User selected "Select Folder"
			if confirmation == 1:
				savePath = ui.chooseFolder(title="TOX Location", start=project.folder)
				pathInfo.update({'pathType' : 'simple'})
				pathInfo.update({'savePath' : savePath})

				makeFolderPrompt = ui.messageBox(makeToxFolderTitle, makeToxFolderMsg, buttons = makeToxFolderBtns)
				# User selected "Yes" to creating a tox folder
				if makeFolderPrompt == 1:
					makeToxFolder = True
				else:
					makeToxFolder = False

				pathInfo.update({'makeToxFolder' : makeToxFolder})


			# User selected "Use Network Path"
			elif confirmation == 2:
				pathInfo = self.GetNetworkPathInfo()
			
			# # User selected "Edit Network Path Settings"
			elif confirmation == 3:
				self.ownerComp.openParameters()

			saveResult = op.ToxTools.ExternalizeComp(comp, pathInfo=pathInfo, backupInfo=backupInfo, doVersion=updateVersions, enableToeBackup=enableToeBackup)
		
		# Comp is already externalized
		else:
			savePath = '/'.join(comp.par.externaltox.val.split('/')[:-1])
			pathInfo.update({'savePath' : savePath})
			saveResult = op.ToxTools.ExternalizeComp(comp, pathInfo, doVersion=updateVersions, backupInfo=backupInfo)
		
		# Generate a pop-up if parent is already external and should be saved and the current comp is newlyExternalized
		parentExt = saveResult.get('parentExternal')
		if newlyExternalized == True:
			if parentExt == True:
				allowParentSave = self.ownerComp.par.Allowparentsave.val

				if allowParentSave:
					confirmation = ui.messageBox(saveParentTitle, saveParentMsg, buttons = saveParentBtns)

					# User selected "Yes" to saving the parent COMP
					if confirmation == 1:
						op.ToxTools.ExternalizeComp(comp.parent(), pathInfo=None)
				else:
					title = "Warning"
					text = "The parent component (" + comp.parent().path + ") will not be saved because parent saving is off.\nYou will need to manually save the parent component to ensure your work is saved."
					btns = ['OK']
					warning = ui.messageBox(title, text, buttons = btns)

	def NetworkDump(self):
		self.scopedCompsDat = self.ownerComp.op('scopedComps')
		pathInfo = self.GetNetworkPathInfo()
		backupInfo = self.GetBackupInfo()
		updateVersions = self.ownerComp.par.Updateversions.val

		saveIgnoreTags = tdu.split(self.ownerComp.par.Netdumpignoretags.eval(), True)
		
		compsToToxify = []

		for row in self.scopedCompsDat.rows()[1:]:
			comp = op(row[0].val)
			if bool(set(comp.tags).intersection(saveIgnoreTags)) == False:
				compsToToxify.append(comp)
		
		for comp in compsToToxify:
			op.ToxTools.ExternalizeComp(comp, pathInfo=pathInfo, backupInfo=backupInfo, doVersion=updateVersions)

	def NetworkDetox(self):
		detoxTitle = 'Network Detox'
		detoxMsg = 'How would you like to detox your current network?'
		detoxBtns = ['Cancel\n', 'Net Dump\nTag(s)', 'Everything under\nRoot COMP']

		rootComp = self.ownerComp.par.Rootcomp.eval()
		detoxIgnoreTags = tdu.split(self.ownerComp.par.Detoxignoretags.eval(), True)
		tagToAppend = self.ownerComp.par.Detoxtag.val

		compsToDetox = []
		externalComps = None

		confirmation = ui.messageBox(detoxTitle, detoxMsg, buttons=detoxBtns)
		
		# User chose to unexternalize Comps including Netdumptags
		if confirmation == 1:
			netDumpTags = tdu.split(self.ownerComp.par.Netdumptags.eval(), True)
			externalComps = rootComp.findChildren(tags=netDumpTags)

		# User chose to unexternalize all externalized Comps under Root COMP
		elif confirmation == 2:
			externalComps = rootComp.findChildren(parValue='*.tox', parName='externaltox')	

		if externalComps != None:
			for comp in externalComps:
				if bool(set(comp.tags).intersection(detoxIgnoreTags)) == False:
					compsToDetox.append(comp)

		for comp in compsToDetox:
			if tagToAppend == '':
				tagToAppend = None
			
			op.ToxTools.UnexternalizeComp(comp, tagToAppend)


	def GetNetworkPathInfo(self):
		pathInfo = {}
		rootComp = self.ownerComp.par.Rootcomp.eval()
		rootFolder = self.ownerComp.par.Rootfolder.eval()
		makeToxFolder = self.ownerComp.par.Maketoxfolder.val

		pathInfo.update({'pathType' : 'networkPath'})
		pathInfo.update({'rootComp' : rootComp})
		pathInfo.update({'rootFolder' : rootFolder})
		pathInfo.update({'makeToxFolder' : makeToxFolder})		

		return pathInfo

	def GetBackupInfo(self):
		saveBackups = self.ownerComp.par.Savebackups.val
		print('!!!!! Save Backups is ', saveBackups)
		backupInfo = None
		if saveBackups:
			backupInfo = {'date':True, 'suffix':None}
		
		return backupInfo

	def GetDirtyComps(self):
		dirtyCompsList = []
		rootComp = self.ownerComp.par.Rootcomp.eval()
		externalComps = rootComp.findChildren(parValue='*.tox', parName='externaltox')
		
		for c in externalComps:
			if c.dirty:
				dirtyCompsList.append([c.path, self.ownerComp.path])

		if rootComp.dirty:
			dirtyCompsList.append([rootComp.path, self.ownerComp.path])

		return dirtyCompsList

	def ShowPackageParameters(self):
		op.ToxTools.openParameters()

	def ShowHelp(self):
		helpDat = op.ToxTools.op('Resources/help_ToxTools_devToxManager')
		helpDat.openViewer()

	def DtmLoadSettings(self):
		#debug("DTM load settings!")
		self.configParser.LoadConfig()

	def DtmSaveSettings(self):
		#debug("DTM save settings!")
		self.configParser.SaveConfig()



### Par Executes ###

	def Networkdump(self, par):
		self.NetworkDump()

	def Detox(self, par):
		self.NetworkDetox()

	def Toxtoolparameters(self, par):
		self.ShowPackageParameters()
	
	def Help(self, par):
		self.ShowHelp()