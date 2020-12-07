import time,random
class Block(object):
	def __init__ (self,prev_hash,merkel_root,timestamp,prev_block=None,mined=False):
		"""Initialize the Blockchain block

		Args:
			prev_hash (int): Hash of the prev block in integer
			merkel_root (int): Random number (for this assignment)
			timestamp (int): Timestamp of block generation
		"""
		self.prev_hash = prev_hash
		self.merkel_root = merkel_root
		self.timestamp = timestamp
		self.prev_block = prev_block
		self.mined = mined

	def __str__(self):
		prev_hash_str = bin(self.prev_hash)[2:]
		prev_hash_str = '0'*(16-len(prev_hash_str)) + prev_hash_str
		merkel_root_str = bin(self.merkel_root)[2:]
		merkel_root_str = '0'*(16-len(merkel_root_str)) + merkel_root_str
		timestamp_str = bin(int(self.timestamp))[2:]
		timestamp_str = '0'*(32-len(timestamp_str)) + timestamp_str
		return hex(int(prev_hash_str + merkel_root_str + timestamp_str,2))



######generate random list########
t = time.time()
b1 = Block(1,2,t)

a_300 = [[b1]]
for i in range(20):
	width = random.randint(1,3)
	l = []
	for j in range(width):
		t = time.time()
		b = Block(random.randint(1,1000),random.randint(1,1000),t,random.choice(a_300[-1]),random.randint(0,1))
		l.append(b)
	a_300.append(l)
############################33

def print_blockchain(a):
	total_blocks = 0
	total_mined_main = 0
	for blist in a:
		total_blocks += len(blist)

	print_list = []

	previous_block = a[-1][0]
	main_string = ""

	for j in range(len(a)):
		i = len(a) - j -1
		list1 = []
		list2 = []
		for x in a[i]:
			if x==previous_block:
				# print(str(x),"hello")
				list1.append(x)
				previous_block = x.prev_block
			else:
				list2.append(x)
		l = list1+list2
		print_list.append(l)

	for j in range(len(print_list)):
		i= len(print_list) - j - 1
		string_out = ""
		first_check = 1
		for x in print_list[i]:
			string_out += str(str(x)) + ":"
			if x.mined:
				string_out+= "1 "
				total_mined_main += first_check
			else:
				string_out+= "0 "
			first_check = 0
		main_string += string_out +"\n"
		# print(string_out)
	return len(a)/total_blocks, total_mined_main/len(a),main_string