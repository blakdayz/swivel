echo "Bootstrapping"
python src/swivel/scanners/ble_scanner.py recreate-db || exit 1
echo "Database created." 
echo "Running the scanners in the background..."
chmod +x ./start_service.sh || exit 1
echo "Starting service..."
./start_service.sh 
