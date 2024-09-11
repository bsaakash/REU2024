#!/usr/bin/env python
# coding: utf-8

# Importing necessary libraries
from pathlib import Path       
import subprocess              
import shlex                   
import os                      
import shutil                  
import pandas as pd            
import numpy as np             


# Function to extract the failure probability from a specified file
def extract_failure_probability(filename="dakotaTab.out"):
    with open(filename, "r") as file:
        data = file.readlines()

    # Process the data into a list of lists and convert to a NumPy array
    big_list = []
    for line in data[1:]:  # Skip the first line
        values = line.split()
        row = [
            float(value) for value in values[2:]
        ]  # Convert values from index 2 onwards to floats
        big_list.append(row)
    data_array = np.array(big_list, dtype=np.float64)

    failure_probability = np.mean(data_array[:, -1])  # Calculate the mean of the last column (failure probabilities)
    return failure_probability, data_array


# Function to configure the analysis based on given variable values
def configure_analysis(var_values_list, filename="templatedir/column_config.py"):
    var_name_list = ["DCR", "L", "e", "section_size", "fire_load_fuel_energy_density"]

    # Reading the template configuration file
    with open(filename, "r") as file:
        data = file.readlines()

    new_data = []
    for line in data:
        for i, var_name in enumerate(var_name_list):
            if f"<{var_name}>" in line:  # Replace placeholders with actual values
                if var_name == "section_size":
                    line = line.replace(f"<{var_name}>", f"'{var_values_list[i]}'")
                else:
                    line = line.replace(f"<{var_name}>", str(var_values_list[i]))
                new_data.append(line)
                break
    # Writing the modified configuration back to the file
    with open(filename, "w") as file:
        file.writelines(new_data)


# Main execution block
if __name__ == "__main__":
    # Change to the directory where the script is located
    os.chdir(Path(__file__).parent)
    
    # Set up source and touch a start file
    source = Path("tmp.SimCenter").resolve()
    Path(source.parent / "start.txt").touch()

    # Read section sizes from a file and store them in a list
    section_size_list = []
    with open("section_sizes.txt", "r") as file:
        sizes = file.readlines()
        for size in sizes:
            section_size_list.append(size.strip())  # Remove any leading/trailing whitespace
    print(f"{section_size_list = }")

    # Define analysis parameters
    eccentricities = [0.0]     # List of eccentricity values
    lengths = [1]              # List of length values
    # DC_ratios = [0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.45, 0.4, 0.35, 0.3]  # List of demand-to-capacity ratios
    DC_ratios = np.arange(0.95, 0, -0.05)  # Range of demand-to-capacity ratios decreasing from 0.95 to 0
    fire_loads = np.arange(4000, 2000, -300)  # Range of fire load values decreasing from 4000 to 2000

    # Loop over each section size
    for section_size in section_size_list:
        res_dict = {}
        for e in eccentricities:
            for L in lengths:
                for DCR in DC_ratios:
                    pf_array = np.zeros(len(fire_loads))  # Initialize an array to store failure probabilities
                    for num, fire_load in enumerate(fire_loads):
                        var_values_list = [DCR, L, e, section_size, fire_load]  # List of current variable values
                        
                        # Prepare directory for analysis
                        destination = source.parent / f"analysis_{num}"
                        if destination.is_dir():
                            shutil.rmtree(destination, ignore_errors=True)
                        shutil.copytree(source, destination)
                        
                        # Change directory to the destination and configure the analysis
                        template_dir = destination / "templatedir"
                        os.chdir(destination)
                        configure_analysis(var_values_list)
                        
                        # Run the analysis using a shell command
                        command = "ibrun dakota -input dakota.in -output dakota.out -error dakota.err"
                        command_list = shlex.split(command)
                        subprocess.run(command_list)
                        
                        # Extract failure probability and store it
                        pf, _ = extract_failure_probability()
                        pf_array[num] = pf
                        
                        # Cleanup after the analysis
                        os.chdir(destination.parent)
                        shutil.rmtree(destination, ignore_errors=True)
                        if pf == 0:  # Stop if failure probability is zero
                            break
                    
                    # Store the results in a dictionary
                    key = f"{section_size}_{e:.3f}_{L}_{DCR:.2f}"
                    val = pf_array
                    res_dict[key] = val
        
        # Convert results dictionary to a DataFrame and save as a CSV file
        res_df = pd.DataFrame(res_dict)
        res_df.insert(0, "fire_load", fire_loads)  # Insert fire load values as the first column
        res_df.to_csv(f"results_{section_size}.csv", index=False)  # Save to CSV

    # Touch a finish file after completing all analyses
    Path(source.parent / "finish.txt").touch()
