NR == 1 {
	print $1
}
NR > 1 {
	print $2
	print $1
	print $1
	print $1
	print $2
}
