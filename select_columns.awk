BEGIN {
    VF = "\t"
}
{
    count = 3;
    printf "%s\t%s" $1 $2;
    for (i=0; i < 13; i++) {
        printf "\t%s\t%s\t%s" $count $(count + 1) $(count +2);
        count = count + 5;
    }
    printf "\n"
}
