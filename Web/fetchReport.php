<?php
header("Content-Type: application/json");

// DB credentials
$host = 'localhost';
$user = 'root';
$password = ''; // make sure this is correct
$database = 'attendance_db';

// Connect to DB
$conn = new mysqli($host, $user, $password, $database);
if ($conn->connect_error) {
    die(json_encode(["error" => "Connection failed: " . $conn->connect_error]));
}

// Get POST data
$startDate = $_POST['startDate'] ?? null;
$endDate = $_POST['endDate'] ?? null;

if (!$startDate || !$endDate) {
    echo json_encode(["error" => "Missing start or end date."]);
    exit;
}

// Prepare query to fetch roll numbers and periods attended within date range
$sql = "SELECT roll_no, periods_attended FROM attendance WHERE date BETWEEN ? AND ?";
$stmt = $conn->prepare($sql);
$stmt->bind_param("ss", $startDate, $endDate);
$stmt->execute();
$result = $stmt->get_result();

// Collect the results
$data = [];
while ($row = $result->fetch_assoc()) {
    $data[] = $row;
}

// Output JSON
echo json_encode($data);

// Cleanup
$stmt->close();
$conn->close();
?>
