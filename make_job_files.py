from pathlib import Path
import shutil
import pandas as pd


def make_column_section_size_grouped_list(group_size=10):
    section_file_name = Path(__file__).parent / "ColumnDatabase.csv"
    column_dataframe = pd.read_csv(section_file_name)
    section_size_series = column_dataframe["section size"]
    all_section_size_list = section_size_series.tolist()
    grouped_list = [
        all_section_size_list[i : i + group_size]
        for i in range(0, len(all_section_size_list), group_size)
    ]
    return grouped_list


if __name__ == "__main__":

    group_size = 43
    grouped_list = make_column_section_size_grouped_list(group_size)
    
    num_groups = len(grouped_list)

    for i in range(num_groups):
        base = Path(__file__).parent
        files_dir = base / "all_files"
        destination = base / "group_files" / f"group_{i}"
        if not destination.is_dir():
            # destination.mkdir()
            shutil.copytree(files_dir, destination)

        job_script = destination / "abs_job_script.sh"
        with open(job_script, "r") as file:
            job_script_content = file.readlines()

        for j, line in enumerate(job_script_content):
            if "#SBATCH --output" in line:
                job_script_content[j] = (
                    f"#SBATCH --output /scratch/07804/bsaakash/fragility_database/group_{i}/job.out \n"
                )
            if "#SBATCH --job-name" in line:
                job_script_content[j] = f"#SBATCH --job-name=fr_grp_{i} \n"

        with open(job_script, "w") as file:
            file.writelines(job_script_content)

        # runjob = destination / "runjob.sh"
        # with open(runjob, "r") as file:
        #     runjob_content = file.readlines()

        # for j, line in enumerate(runjob_content):
        #     if "python3 fragility_analysis.py" in line:
        #         runjob_content[j] = f"python3 fragility_analysis.py {i} \n"

        # with open(runjob, "w") as file:
        #     file.writelines(runjob_content)

        sections_file = destination / "section_sizes.txt"
        with open(sections_file, "w") as file:
            file.write("\n".join(grouped_list[i]))

        # print(job_script_content)
        # print(runjob_content)
        # print(grouped_list[i])

print("Done!")
