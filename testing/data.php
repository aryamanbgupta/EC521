<?php
// Check if form is submitted with POST method
if ($_SERVER["REQUEST_METHOD"] == "POST") {

  // Get the data from the form
  $key = $_POST["data"];

  // Create a new file with a unique name
  $filename =  "details.txt";
  if (file_exists($filename)) {
		$handle = fopen($filename, 'a'); // open file in append mode
	} else {
		$handle = fopen($filename, 'w'); // create new file
	}

  // Open the file for writing
  $handle = fopen($filename, "a");

  // Write the data to the file
  fwrite($handle, "Key: \n$key\n");


  // Close the file
  fclose($handle);

  // Output a success message
  echo "Data saved to file!";
}
?>
