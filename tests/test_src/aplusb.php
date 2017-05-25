<?php
function solveMeFirst($a,$b){
  // Hint: Type return $a + $b; below
  return $a + $b;
}
$handle = fopen ("php://stdin","r");
$_a = fgets($handle);
$_b = fgets($handle);
$sum = solveMeFirst((int)$_a,(int)$_b);
print ($sum);
fclose($handle);
?>
