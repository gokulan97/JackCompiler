keyword = set(['class', 'constructor', 'function', 'method', 'field', 'static', 'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while', 'return'])
symbol = ['(', ')', '{', '}', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~']
ids = set()
className = str()
classTable = [0]
subroutineTable = [0]
subroutineList = []
field_count = static_count = 0

def check_identifier(token):
	if len(token) > 0:
		if token[0].isdigit():
			return False
		for i in range(0, len(token)):
			if not token[i].isalnum() or token[i] == '_':
				return False
		return True
	return False

def token_type(li):
	if len(li) == 0:
		return
	if li[0].strip() in keyword:
		return 'keyWord'
	elif li[0].strip() in symbol:
		return 'symbol'
	elif li[0].strip().find('\"') != -1:
		if li[len(li)-1] == '\"':
			return 'string'
	else:
		try:
			integer = int(li[0].strip())
			if integer in range(0, 32768):
				return 'intVal'
		except ValueError:
			if check_identifier(li[0].strip()):
				return 'identifier'

def compileClass(li):
	global className
	outStream.write('<class>\n')
	if li[0] == 'class':
		keyWord(li[0])
	else:
		print("Error: Expected identifier class")

	if check_identifier(li[1]):
		className = li[1]
		identifier(li[1])

	if li[2] == '{':
		Symbol(li[2])
		li = li[3:]
	while li[0] != '}':
		if li[0] in ['static', 'field']:
			li = compileClassVarDec(li[:])
		elif li[0] in ['function', 'method', 'constructor']:
			li = compileSubRoutineDec(li[:])

	Symbol('}')
	outStream.write('</class>\n')

def compileClassVarDec(li):
	global field_count, static_count
	global classTable
	outStream.write('<classVarDec>\n')
	if li[0] == 'field':
		field_count += 1
	elif li[0] == 'static':
		static_count += 1
	
	kind = li[0]
	keyWord(kind)
	if li[1] in ['int', 'char', 'boolean']:
		keyWord(li[1])
	elif li[1] in [className, 'Array', 'String']:
		identifier(li[1])
	typ = li[1]
	if check_identifier(li[2]):
		varName = li[2]
		identifier(varName)
	else:
		print('Expected Identifier')
	Define(varName, typ, kind, classTable)

	i=3
	while li[i] == ',':
		Symbol(li[i])
		i+=1
		if check_identifier(li[i]):
			varName = li[i]
			i += 1
		else:
			print('Expected Identifier')
		Define(varName, typ, kind, classTable)
		identifier(varName)

	if li[i] == ';':
		Symbol(li[i])
	outStream.write('</classVarDec>\n')
	return li[i+1:]

def compileSubRoutineDec(li):
	global subroutineTable,className, subroutineList
	varCount = argCount = 0
	outStream.write('<subroutineDec>\n')

	if li[0] in ['constructor', 'method', 'function']:
		keyWord(li[0])
	
	if li[1] in ['void', 'char', 'boolean', 'int']:
		keyWord(li[1])
	elif li[1] in [className, 'Array', 'String']:
		identifier(li[1])

	if check_identifier(li[2]):
		subroutineName = li[2]
		identifier(li[2])

	subroutineList.append(subroutineName)
	if li[3] == '(':
		Symbol(li[3])

	if li[0] in ['method']:
		Define('this', className, 'argument', subroutineTable)
		oStream.write('push argument 0\npop pointer 0\n')
	elif li[0] == 'constructor':
		oStream.write('push constant {}\n'.format(varCount('field')))
		oStream.write(' call Memory.alloc 1\n')
		oStream.write('pop pointer 0\n')
	li = compileParameterList(li[4:])

	if li[0] == ')':
		Symbol(li[0])
		
	outStream.write('<subroutineBody>\n')
	if li[1] == '{':
		Symbol(li[1])
	li = li[2:]
	count = 0
	while li[0] == 'var':
		li = compileVarDec(li)
		count += 1
	oStream.write('function {}.{} {}'.format(className, subroutineName, count))
	li = compileStatements(li)
	
	Symbol(li[0])
	outStream.write('</subroutineBody>\n')

	outStream.write('</subroutineDec>\n')
	print(subroutineTable)
	subroutineTable = [0]
	return li

def compileParameterList(li):
	global subroutineTable, className
	while li[0] != ')':
		if li[0] in ['int', 'char', 'boolean']:
			keyWord(li[0])
			typ = li[0]
		elif li[0] in ['Array', 'String', className]:
			identifier(li[0])
			typ = li[0]

		if check_identifier(li[1]):
			varName = li[1]
			identifier(varName)

		Define(varName, typ, 'argument', subroutineTable)
		if li[2] == ',':
			Symbol(li[2])
			li = li[3:]
		else:
			li = li[2:]
	return li

def compileVarDec(li):
	global subroutineTable
	outStream.write('<VarDec>\n')
	if li[0] == 'var':
		keyWord(li[0])

	if li[1] in ['char', 'int', 'boolean']:
		keyWord(li[1])
	elif li[1] in [className, 'Array', 'String']:
		identifier(li[1])
	typ =  li[1]
	if check_identifier(li[2]):
		identifier(li[2])
		varName = li[2]
		Define(varName, typ, 'local', subroutineTable)
	li = li[3:]
	i=0
	while li[i] == ',':
		Symbol(li[i])
		i+= 1
		if check_identifier(li[i]):
			identifier(li[i])
			varName = li[i]
		Define(varName, typ, 'local', subroutineTable)
		i+=1

	if li[i] == ';':
		Symbol(li[i])
	outStream.write('</VarDec>\n')
	return li[i+1:]

def compileStatements(li):
	outStream.write('<statements>\n')
	while li[0] in ['let', 'do', 'while', 'if', 'return']:
		if li[0] == 'let':
			li = compileLetStatement(li)
		if li[0] == 'do':
			li = compileDoStatement(li)
		if li[0] == 'while':
			li = compileWhileStatement(li)
		if li[0] == 'if':
			li = compileIfStatement(li)
		if li[0] == 'return':
			li = compileReturnStatement(li)
	outStream.write('</statements>\n')
	return li

def compileLetStatement(li):
	outStream.write('<letStatement>\n')
	if li[0] == 'let':
		keyWord(li[0])
	if check_identifier(li[1]):
		x = search(subroutineTable, li[1])
		if x == -1:
			x = search(classTable, li[1])
			if x == -1:
				print('Variable not declared')
				return
	oStream.write("push {} {}\n".format(x[2], x[3]) )

	if li[2] == '=':
		li = compileExpression(li[3:])
		oStream.write('pop {} {}\n'.format(x[2], x[3]))
		if li[0] == ';':
			Symbol(li[0])

	elif li[2] == '[' and x[1] == 'Array':
		li = compileExpression(li[3:])
		if li[0] == ']':
			oStream.write('add\npop pointer 1\n')
		else:
			print('Symbol \']\' expected')
			return
		li = li[1:]
		if li[0] == '=':
			Symbol(li[0])
			li = compileExpression(li[1:])
			if li[0] == ';':
				Symbol(li[0])
		oStream.write('pop that 0\n')

	outStream.write('</letStatement>\n')
	return li[li.index(';')+1:]

def compileExpression(li):
	outStream.write('<expression>\n')
	li = compileTerm(li)
	while li[0] in symbol:
		if li[0] == ';':
			break
		op = li[0]
		Symbol(op)
		li = compileTerm(li[1:])
		if op == '+':
			oStream.write('add\n')
		elif op == '-':
			oStream.write('sub\n')
		elif op == '*':
			oStream.write('call Math.multiply 2\n')
		elif op == '/':
			oStream.write('call Math.divide 2\n')
		elif op == '&':
			oStream.write('and\n')
		elif op == '|':
			oStream.write('or\n')
		elif op == '<':
			oStream.write('lt\n')
		elif op == '>':
			oStream.write('gt\n')
		elif op == '=':
			oStream.write('eq\n')
	outStream.write('</expression>\n')
	return li[1:]

def compileTerm(li):
	global classTable, subroutineTable
	token = token_type(li[0])
	if li[0] == ';':
		Symbol(li[0])
		return li[1:]
	if token == 'intVal':
		oStream.write('push constant {}\n'.format(li[0]))
		return li[1:]
	elif token == 'string':
		length = len(li[0])
		oStream.write('push constant {}\ncall String.new 1\n'.format(length-2))
		for i in range(1, length-1):
			oStream.write('push constant {}\ncall String.appendChar 1\n'.format(ord(li[0][i])))
		return li[1:]
	elif token == 'keyWord':
		if li[0] == 'true':
			oStream.write('push constant 1\nneg\n')
		elif l[0] == 'false' or l[0] == 'null':
			oStream.write('push constant 0\n')
		elif l[0] == 'this':
			oStream.write('push argument 0\n')
		return li[1:]
	elif token == 'identifier':
		x = search(subroutineTable, li[0])
		if x == -1:
			x = search(classTable, li[0])
			if x == -1:
				if li[0] in subroutineList and li[1] == '(':
					arb_tuple = compileExpressionList(li[2:])
					n_arg = arb_tuple[0]
					li = arb_tuple[1]
					if li[0] != ')':
						pass#handle error
					oStream.write('call ')
		if li[1] not in ['.', '[']:
			oStream.write('push {} {}\n'.format( x[2], x[3]) )
			return li[1:]
		elif li[1] == '[':
			li = compileExpression(li[2:])
			oStream.write('push {} {}\nadd\npop pointer 1\npop that 0\n'.format(x[2], x[3]))
			if li[0] == ']':
				pass
			return li[1:]
		elif li[1] == '.':
			subroutineName = li[2]
			if li[3] != '(':
				pass#Handle the error
			oStream.write('push {} {}\n'.format(x[2], x[3]))
			arb_tup = compileExpressionList(li[4:])
			num = arb_tup[0]
			li = arb_tup[1]
			if li[0] != ')':
				pass#Handle error
			oStream.write('call {}.{} {}\n'.format(x[1], subroutineName, num))
			return li[1:]
	elif li[0] in ['~', '-']:
		if li[0] == '~':
			oStream.write('neg\n')
		else:
			oStream.write('not\n')

def compileExpressionList(li):
	count = 0
	while True:
		if li[0] == ')':
			break
		li = compileExpression(li[:])
		count += 1
		if li[0] == ',':
			li = li[1:]
	return (count, li)

def compileIfStatement(li):
	if li[0] != 'if':
		pass#handle
	if li[1] != '(':
		pass#handle
	li = compileExpression(li[2:])
	if li[0] != ')':
		pass
	if li[1] != '{':
		pass
	oStream.write('neg\nif-goto L1\n')
	li = compileStatements()
	if li[0] != '}':
		pass
	oStream.write('goto L2\n')
	if li[1] == 'else':
		oStream.write('label L1\n')
		if li[2] != '{':
			pass
		li = compileStatements(li[3:])
		if li[0] != '}':
			pass
		oStream.write('label L2\n')
		return li[1:]
	else:
		return li

def compileReturnStatement(li):
	if li[0] == 'return':
		if li[1] == ';':
			oStream.write('push constant 0\nreturn\n')
		else:
			li = compileExpression(li)
			if li[0] == ';':
				return li[1:]
		return li[2:]

def compileDoStatement(li):
	if li[0] != 'do':
		pass#handle

def compileWhileStatement(li):
	oStream.write('label L1\n')
	if li[0] != 'while' and li[1] != '(':
		pass
	li = compileExpression(li[2:])
	if li[0] != ')':
		pass
	oStream.write('neg\nif-goto L2\n')
	if li[1] != '{':
		pass
	li = compileStatements(li[2:])
	oStream.write('goto L1\nlabel L2\n')
	if li[0] != '}':
		pass
	return li[1:]

def Define(varname, typ, kind, table):
	table.append([varname, typ, kind, table[0]])
	table[0] += 1
	return

def search(table, varName):
	for i in range(1, len(table)):
		if table[i][0] == varName:
			return table[i]
	return -1

def keyWord(token):
	outStream.write('<keyword>{}</keyword>\n'.format(token))

def Symbol(token):
	outStream.write("<symbol>{}</symbol>\n".format(token))

def intVal(token):
	outStream.write("<integerConstant>{}</integerConstant>\n".format(token))

def identifier(token):
	outStream.write("<identifier>{}</identifier>\n".format(token))

if __name__ == '__main__':
	file = input()
	
	try:
		inStream = open(file+'.jack', 'r')
	except FileNotFoundError:
		print("{}.jack : File not found".format(file))

	outStream = open(file+'.xml', 'w')
	oStream = open(file+'.vm', 'w')

	lines = list()
	for line in inStream:
		lines.append(line)

	i=0
	li = list()
	while i <len((lines)):
		line = lines[i]
		if line.find('//') != -1:
			line = line[:line.find('//')]
		elif line.find('/*') != -1:
			while line.find('*/') == -1:
				 i +=1
				 line = lines[i]
			else:
				tempLine = ''
				if line.find('/*') != -1:
					tempLine = line[:line.find('/*')]
				line = tempLine + line[line.find('*/')+2:]

		if line.find('\"') == -1:	
			l = line.strip().split(' ')
			for k in range(0, len(l)):
				l[k] = l[k].strip()
				token = ''
				j=0
				while j<len(l[k]):
					while j<len(l[k]) and l[k][j] not in symbol:
						token += l[k][j]
						j += 1
					else:
						li.append(token.strip())
						if j<len(l[k]):
							li.append(l[k][j])
						token=''
						j += 1
		i+= 1

	try:
		while 1:
			li.remove('')
	except ValueError:
		pass

	print(li)
	stack = list()
	tab = 0

	li = compileClass(li)
	print(classTable)
		
	outStream.close()
	inStream.close()
