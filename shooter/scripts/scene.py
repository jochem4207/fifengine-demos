# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

from fife import fife
from scripts.ships.shipbase import Ship
from scripts.ships.player import Player
from scripts.ships.enemies import *
from scripts.common.helpers import Rect

class SceneNode(object):
	def __init__(self, spaceobjects = None):
		if not spaceobjects:
			self._spaceobjects = list()
		else:
			self._spaceobjects = spaceobjects
		
	def _getObjects(self):
		return self._spaceobjects
		
	def _setObjects(self, spaceobjects):
		self._spaceobjects = spaceobjects
		
	spaceobjects = property(_getObjects, _setObjects)

class Scene(object):
	def __init__(self, world, engine, objectLayer):
		self._engine = engine
		self._world = world
		self._model = engine.getModel()
		self._layer = objectLayer
		self._nodes = list()
		
		self._player = None
		self._projectiles = list()
		
		self._maxnodes = 128
		self._xscale = 0
		
		self._time = 0
		self._timedelta = 0
		self._lasttime = 0
		
		self._xscale = self._layer.getCellGrid().getXScale()
		self._yscale = self._layer.getCellGrid().getYScale()
		
		self._paused = False
		self._timemod = 0
		
		self._gameover = False
		
		self._boss = None

	def destroyScene(self):
		nodestodelete = list()
		objtodelete = list()
	
		for node in self._nodes:
			nodestodelete.append(node)
			for obj in node.spaceobjects:
				objtodelete.append(node)
			
			for obj in objtodelete:
				if obj in node.spaceobjects:
					node.spaceobjects.remove(obj)
				
			objtodelete = list()
					
		for node in nodestodelete:
			if node in self._nodes:
				self._nodes.remove(node)
			
		self.removeAllProjectiles()

	def initScene(self, mapobj):
		#initialize our scene array to some arbitrary size
		for i in range(0,self._maxnodes):
			self._nodes.append(SceneNode())

		self._boss = None

		self._player = Player(self, 'player')
		self._player.init()
		self._player.start()

		enemies = list()
		
		temp = self._layer.getInstances('dodge1')
		enemies.extend(temp)

		temp = self._layer.getInstances('dodge2')
		enemies.extend(temp)

		temp = self._layer.getInstances("diag_top_right")
		enemies.extend(temp)

		temp = self._layer.getInstances("diag_bottom_right")
		enemies.extend(temp)

		temp = self._layer.getInstances("streaker")
		enemies.extend(temp)

		temp = self._layer.getInstances("boss")
		enemies.extend(temp)

		for instance in enemies:
			objectName = instance.getId()
			print objectName
			
			if objectName == "dodge1":
				enemy = Saucer1(self, 'enemy', instance, False)
			elif objectName == "dodge2":
				enemy = Saucer2(self, 'enemy', instance, False)
			elif objectName == "diag_top_right":
				enemy = DiagSaucer(self, 'enemy', 0, instance, False)
			elif objectName == "diag_bottom_right":
				enemy = DiagSaucer(self, 'enemy', 1, instance, False)
			elif objectName == "streaker":
				enemy = Streaker(self, 'enemy', instance, False)
			elif objectName == "boss":
				enemy = Boss(self, 'enemy', instance, False)
				self._boss = enemy
			else:
				enemy = Ship(self, 'enemy', instance, False)
				
			enemy.start()

			loc = instance.getLocation().getExactLayerCoordinates()
			nodeindex = int(loc.x * self._xscale)
			enemy.scenenodeid = nodeindex
			self._nodes[nodeindex].spaceobjects.append(enemy)
			
		#and finally add the player to the scene
		self.addObjectToScene(self._player)
		
		self.startCamera()
		
	def pause(self, time):
		self._pausedtime = time
		self._paused = True
		
	def unpause(self, time):
		self._timemod += time - self._pausedtime
		self._paused = False
		
	def playerHit(self):
		self._player.destroy()
		if self._player.lives <= -1:
			self._gameover = True
			self._world.gameOver()
			#self.removeAllProjectiles()
			return

		#self._player.setInvulnerable(2)
		
	def endLevel(self):
		self._world.endLevel()
		
	def removeAllProjectiles(self):
		projtodelete = list()
		for p in self._projectiles:
			p.destroy()
			projtodelete.append(p)
			
		for p in projtodelete:
			if p in self._projectiles:
				self._projectiles.remove(p)		

	def getObjectsInNode(self, nodeindex):
		return self._nodes[nodeindex].instances

	def getObjectsInRange(self, rangeL, rangeR):
		objects = list()
		
		for i in range(rangeL, rangeR):
			objects.extend(self._nodes[i].spaceobjects)
			
		return objects
		
	def addObjectToScene(self, obj):
		#TODO: search to ensure the object isn't already part of the scene
		loc = obj.instance.getLocation().getExactLayerCoordinates()
		nodeindex = int(loc.x * self._xscale)
		
		self._nodes[nodeindex].spaceobjects.append(obj)
		obj.scenenodeid = nodeindex		

	def addProjectileToScene(self, projectile):
		self._projectiles.append(projectile)
	
	def moveObjectInScene(self, obj):
		loc = obj.instance.getLocation().getExactLayerCoordinates()
		nodeindex = int(loc.x * self._xscale)
		
		if nodeindex != obj.scenenodeid:
			self._nodes[obj.scenenodeid].spaceobjects.remove(obj)
			self._nodes[nodeindex].spaceobjects.append(obj)
			obj.scenenodeid = nodeindex
	
	def removeObjectFromScene(self, obj):
		for node in self._nodes:
			if obj in node.spaceobjects:
				node.spaceobjects.remove(obj)
				return
	
	def attachCamera(self, cam):
		self._camera = cam
		self._camera.setLocation(self._player.location)
	
	def stopCamera(self):
		self._cameraspeed = 0
		
	def startCamera(self):
		self._cameraspeed = 0.001
	
	def update(self, time, keystate):
		timedelta = (time - self._timemod) - self._time
		self._timedelta = timedelta
		self._time = time - self._timemod
		
		self._keystate = keystate
		
		#update camera location
		loc = self._camera.getLocation()
		exactloc = self._camera.getLocation().getExactLayerCoordinates()
		#slowly move to the right
		exactloc.x += timedelta * self._cameraspeed
		loc.setExactLayerCoordinates(exactloc)
		self._camera.setLocation(loc)
		
		topleft = self._camera.toMapCoordinates(fife.ScreenPoint(0,0))
		bottomright = self._camera.toMapCoordinates(fife.ScreenPoint(1024,768))
		
		#which scene nodes to use to update objects
		leftnode = int(topleft.x)
		rightnode = int(bottomright.x) + 1
		
		#get a list of objects on the screen
		if leftnode < 0:
			leftnode = 0
		if rightnode > self._maxnodes:
			rightnode = self._maxnodes
		screenlist = self.getObjectsInRange(leftnode, rightnode)

		#update objects on the screen
		for obj in screenlist:
			if obj == self._boss:
				if bottomright.x > ((self._boss.location.getExactLayerCoordinates().x * self._xscale) + 0.5):
					self.stopCamera()

			if not (obj == self._player and self._gameover):
				obj.update()
			
			if obj.changedposition:
				self.moveObjectInScene(obj)

			if obj != self._player:
				#TODO: enemy should fire weapon in their update function
				if obj.running:
					obj.fire(fife.DoublePoint(-1,0))
			
				if obj.running and obj.boundingbox.intersects(self._player.boundingbox):
					#player touched an enemy.  Destroy player and 
					#re-initialize scene
					if not self._player.invulnerable:
						self.playerHit()
						obj.destroy()
						
#			self._world.renderBoundingBox(obj)
					
		
		
		#update the list of projectiles
		projtodelete = list()
		for p in self._projectiles:
			p.update()
			#check to see if the projectile hit any object on the screen
			for o in screenlist:
				#cant get hit by your own bullet
				if p.owner != o:
					if o.running and p.boundingbox.intersects(o.boundingbox):
						if o != self._player and p.owner.isplayer:
							o.applyHit(p.damage)
							#check if enemy ship was destroyed
							if not o.running:
								self._player.applyScore(o.scorevalue)
							p.destroy()
						elif o == self._player:
							#player got hit by a projectile
							if not self._player.invulnerable:
								p.destroy()
								self.playerHit()
			
#			self._world.renderBoundingBox(p)
							
			
			#build a list of projectiles to remove (ttl expired)
			if not p.running:
				projtodelete.append(p)

		#remove any expired projectiles 
		for p in projtodelete:
			if p in self._projectiles:
				self._projectiles.remove(p)

				
	def _getPlayer(self):
		return self._player
		
	def _getKeyState(self):
		return self._keystate
		
	def _getCamera(self):
		return self._camera
		
	def _getObjectLayer(self):
		return self._layer
		
	def _getModel(self):
		return self._model
		
	def _getTime(self):
		return self._time
	
	def _getTimeDelta(self):
		return self._timedelta
		
	def _getPaused(self):
		return self._paused
		
	player = property(_getPlayer)
	keystate = property(_getKeyState)
	camera = property(_getCamera)
	objectlayer = property(_getObjectLayer)
	model = property(_getModel)
	time = property(_getTime)
	timedelta = property(_getTimeDelta)
	paused = property(_getPaused)	
