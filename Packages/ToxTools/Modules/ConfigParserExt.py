"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""

from TDStoreTools import StorageManager
TDF = op.TDModules.mod.TDFunctions

class ConfigParserExt():
	"""
	Config Parser Extension
	"""
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.configPars = self.ownerComp.op('pars')
		self.configFolderPaths = self.ownerComp.op('paths')

		
	def LoadConfig(self, loadPars = True, loadPaths = True):
			
			#kick all config inputs
			for fOp in self.ownerComp.findChildren(tags = ['configFile']):
				fOp.par.refreshpulse.pulse()
				fOp.cook(force = True, recurse = True)	
			
			if loadPaths:
				self.SetFolderPaths(self.configFolderPaths)
			
			if loadPars:
				self.SetConfigPars(self.configPars, root = self.ownerComp.par.Rootcomp.eval())

	def SetFolderPaths(self, dat):
		foldersTable = dat
		for entry in foldersTable.rows():
			project.paths[entry[0].val] = entry[1].val
			print('setting project folder path ', project.paths[entry[0].val])

	def SetConfigPars(self, dat, root = None, ignoreNames = []):
		#print('par config setting starting')
		for entry in dat.rows()[1:]:
			opKey = entry[0].val
			targOp = None
			if (targOp is None) and (root is not None):
				targOp = root.op(opKey)
			if targOp is None:
				#if hasattr(op, opKey):
				targOp = getattr(op, opKey, None)
			if targOp:
				parName = entry[1].val
				if parName not in ignoreNames:
					val = entry[2].val
					if hasattr(targOp.par, parName):
						print('setting ', targOp.path, ':par: ', parName, ' to : ', val)
						targPar = getattr(targOp.par, parName)
						# stupid cool check, need to get in true json or string par checker
						if (val != "True"):
							if (val != "False"):
								targPar.val = val
							else:
								targPar.val = False
						else:
							targPar.val = True
					else:
						print('op ', targOp.path, ' does not have par: ', parName)

		print('par config setting complete complete for ', self.ownerComp.path)

	def PathRelative(self, path):
		"""
		returns the path relative to the parser's scoped Root
		"""	
		rootComp = self.ownerComp.par.Rootcomp.eval()
		target = op(path)
		retPath = path
		if rootComp and target:	
			if rootComp == target:
				retPath = '.'
			else:
				retPath = rootComp.relativePath(op(path))
			if TDF.parentLevel(rootComp, target) is None:
				retPath = '../'+retPath	
		
		return retPath
	
	def SaveConfig(self):
		self.ownerComp.op('configFileOut').par.write.pulse()


	def Loadconfig(self, par):
		self.LoadConfig()

	def Saveconfig(self, par):
		self.SaveConfig()

