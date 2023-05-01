BEGIN {
    rta4 = 0;
    rta4u = 0;
    greather_count = 0;
    equal_count = 0;
    leaser_count = 0;
    dif_when_greater = 0;
    dif_when_leaser = 0;
    rta4_count = 0;
    rta4u_count = 0;
    count = 0;
}
$1 == "RTA4" {
    rta4 = int($2);
    rta4_count += rta4;
    count += 1;
}
$1 == "RTA4a" {
    rta4u = int($2);
    rta4u_count += rta4u;
    if (rta4 < rta4u) {
        greather_count += 1;
        dif_when_greater += (rta4u - rta4);
    }
    else if (rta4 == rta4u) 
        equal_count += 1;
    else {
        leaser_count += 1;
        dif_when_leaser += (rta4 - rta4u);
    }
}
END {
    print (rta4_count / count) " " (rta4u_count / count) " " greather_count " " equal_count " " leaser_count " " (dif_when_greater / greather_count) " " (dif_when_leaser / leaser_count);
}
