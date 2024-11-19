echo "Bootstrapping"
echo "Running the scanners in the background..."
python src/swivel/scanners/ble_scanner.py run-scanner &
python main.py || exit 1
echo "Script exiting"
