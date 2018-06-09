from PyQt5 import QtCore, QtGui, uic, QtWidgets
import math
import time

class CodeUIEdgeItem(QtWidgets.QGraphicsItem):
	def __init__(self, srcUniqueName, tarUniqueName, edgeData = {}, parent = None, scene = None):
		super(CodeUIEdgeItem, self).__init__(parent)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
		self.setAcceptHoverEvents(True)
		self.srcUniqueName = srcUniqueName
		self.tarUniqueName = tarUniqueName
		self.setZValue(-1)
		self.path = None
		self.pathShape = None
		self.curve = None
		self.pathPnt = None

		self.file = ''
		self.line = -1
		self.column = -1
		dbRef = edgeData.get('dbRef', None)
		if dbRef:
			self.file = dbRef.file().longname()
			self.line = dbRef.line()
			self.column = dbRef.column()

		self.isHover = False

		# (number, point)
		self.orderData = None
		self.buildPath()
		self.isConnectedToFocusNode = False
		self.schemeColorList = []
		self.customEdge = edgeData.get('customEdge', False)
		self.isCandidate = False

	def getNodePos(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		srcNode = scene.getNode(self.srcUniqueName)
		tarNode = scene.getNode(self.tarUniqueName)
		if not srcNode or not tarNode:
			return QtCore.QPointF(), QtCore.QPointF()
		srcPos = srcNode.pos()
		tarPos = tarNode.pos()
		return (srcNode.getRightSlotPos(), tarNode.getLeftSlotPos())

	def getNodeCenterPos(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		srcNode = scene.getNode(self.srcUniqueName)
		tarNode = scene.getNode(self.tarUniqueName)
		if not srcNode or not tarNode:
			return QtCore.QPointF(), QtCore.QPointF()
		return srcNode.pos(), tarNode.pos()

	def getMiddlePos(self):
		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		srcNode = scene.getNode(self.srcUniqueName)
		tarNode = scene.getNode(self.tarUniqueName)
		if not srcNode or not tarNode:
			return QtCore.QPointF()
		return (srcNode.pos() + tarNode.pos()) * 0.5

	def boundingRect(self):
		srcPos, tarPos = self.getNodePos()
		minPnt = (min(srcPos.x(), tarPos.x()), min(srcPos.y(), tarPos.y()))
		maxPnt = (max(srcPos.x(), tarPos.x()), max(srcPos.y(), tarPos.y()))

		return QtCore.QRectF(minPnt[0], minPnt[1], maxPnt[0]-minPnt[0], maxPnt[1]- minPnt[1])

	def getNumberRect(self):
		if self.orderData:
			pnt = self.orderData[1]
			rect = QtCore.QRectF(pnt.x()-10, pnt.y()-10,20,20)
			return rect
		return QtCore.QRectF()

	def pointAtPercent(self, t):
		return self.curve.pointAtPercent(t)

	def buildPath(self):
		srcPos, tarPos = self.getNodePos()
		if self.pathPnt and (self.pathPnt[0]-srcPos).manhattanLength() < 0.05 and (self.pathPnt[1]-tarPos).manhattanLength() < 0.05:
			return self.path
		self.pathPnt = (srcPos, tarPos)
		path = QtGui.QPainterPath()
		path.moveTo(srcPos)
		dx = tarPos.x() - srcPos.x()
		p1 = srcPos + QtCore.QPointF(dx*0.3, 0)
		p2 = tarPos + QtCore.QPointF(-dx*0.7, 0)
		path.cubicTo(p1,p2,tarPos)
		self.curve = QtGui.QPainterPath(path)
		self.path = path

		from PyQt5.QtGui import QPainterPathStroker
		stroker = QPainterPathStroker()
		stroker.setWidth(10.0)
		self.pathShape = stroker.createStroke(self.path)
		return path

	def findCurveYPos(self, x):
		if not self.pathPnt:
			return 0.0
		if not self.curve:
			minY = min(self.pathPnt[0].y(), self.pathPnt[1].y())
			maxY = max(self.pathPnt[0].y(), self.pathPnt[1].y())
			return (minY + maxY) * 0.5
		sign = 1.0 if self.pathPnt[1].x() > self.pathPnt[0].x() else -1.0
		minT = 0.0
		maxT = 1.0
		minPnt = self.curve.pointAtPercent(minT)
		maxPnt = self.curve.pointAtPercent(maxT)
		for i in range(8):
			midT = (minT + maxT) * 0.5
			midPnt = self.curve.pointAtPercent(midT)
			if (midPnt.x() - x) * sign < 0:
				minT = midT
				minPnt = midPnt
			else:
				maxT = midT
				maxPnt = midPnt
			if abs(minPnt.y() - maxPnt.y()) < 0.01:
				break
		return (minPnt.y() + maxPnt.y()) * 0.5

	def isXBetween(self, x):
		if not self.pathPnt:
			return False
		if not self.curve:
			minX = min(self.pathPnt[0].x(), self.pathPnt[1].x())
			maxX = max(self.pathPnt[0].x(), self.pathPnt[1].x())
			return x > minX and x < maxX
		minPnt = self.curve.pointAtPercent(0)
		maxPnt = self.curve.pointAtPercent(1)
		return x > min(minPnt.x(), maxPnt.x()) and x < max(minPnt.x(), maxPnt.x())

	def shape(self):
		#srcPos, tarPos = self.getNodePos()
		#path = QtGui.QPainterPath()
		# path.moveTo(srcPos)
		# path.lineTo(tarPos)
		#path.addRect(self.boundingRect())
		#return path
		path = QtGui.QPainterPath(self.pathShape)
		if self.orderData:
			pnt = self.orderData[1]
			rect = self.getNumberRect()
			path.addEllipse(rect)
		return path

	def paint(self, painter, styleOptionGraphicsItem, widget_widget=None):
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		clr = QtCore.Qt.darkGray if self.isSelected() else QtCore.Qt.lightGray

		srcPos, tarPos = self.getNodeCenterPos()
		isReverse = srcPos.x() > tarPos.x()
		isHighLight = False
		if self.isSelected() or self.isHover:
			clr = QtGui.QColor(255,157,38,255)
			isHighLight = True
		else:
			if isReverse:
				clr = QtGui.QColor(159,49,52,200)
			else:
				clr = QtGui.QColor(150,150,150,100)

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		penStyle = QtCore.Qt.SolidLine
		penWidth = 3.0
		pen = QtGui.QPen(clr, penWidth, penStyle, QtCore.Qt.FlatCap)

		if self.schemeColorList:
			if isHighLight:
				pen.setWidthF(9.0)
				painter.setPen(pen)
				painter.drawPath(self.path)
			elif self.isCandidate:
				pen.setColor(QtGui.QColor(183,101,0,200))
				pen.setWidthF(9.0)
				pen.setStyle(QtCore.Qt.SolidLine)
				painter.setPen(pen)
				painter.drawPath(self.path)
			dash = 5
			pen = QtGui.QPen(clr, 3.0, QtCore.Qt.CustomDashLine, QtCore.Qt.FlatCap)
			pen.setDashPattern([dash, dash*(len(self.schemeColorList)-1)])
			for i, schemeColor in enumerate(self.schemeColorList):
				pen.setDashOffset(i*dash)
				pen.setColor(schemeColor)
				painter.setPen(pen)
				painter.drawPath(self.path)
		else:
			if isHighLight:
				pen.setWidthF(9.0)
			elif self.isCandidate:
				pen.setColor(QtGui.QColor(183,101,0,200))
				pen.setWidthF(9.0)
				pen.setStyle(QtCore.Qt.SolidLine)
			painter.setPen(pen)
			painter.drawPath(self.path)

		if self.orderData is not None:
			order = self.orderData[0]
			rect = self.getNumberRect()
			painter.setBrush(clr)
			painter.setPen(QtCore.Qt.NoPen)
			painter.drawEllipse(rect)
			painter.setPen(QtGui.QPen(QtGui.QColor(0,0,0), 2.0))

			textFont = QtGui.QFont('tahoma', 12)
			painter.setFont(textFont)
			painter.drawText(rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter, '%s' % order)
		endTime = time.time()

	def getCallOrder(self):
		if self.orderData:
			return self.orderData[0]
		return None

	def hoverLeaveEvent(self, QGraphicsSceneHoverEvent):
		super(CodeUIEdgeItem, self).hoverLeaveEvent(QGraphicsSceneHoverEvent)
		self.isHover = False

	def hoverEnterEvent(self, QGraphicsSceneHoverEvent):
		super(CodeUIEdgeItem, self).hoverEnterEvent(QGraphicsSceneHoverEvent)
		self.isHover = True

	def mouseDoubleClickEvent(self, event):
		super(CodeUIEdgeItem, self).mouseDoubleClickEvent(event)

		from UIManager import UIManager
		scene = UIManager.instance().getScene()
		if scene:
			scene.showInEditor()