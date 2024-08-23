#!/bin/bash                                                                                                                                                                                    
                                                                                                                                                   
# Slurm directives.                                                                                                                                                                            
#SBATCH --account DesignSafe-SimCenter                                                                                                                                                         
#SBATCH --job-name tapisjob.sh                                                                                                                                                                 
#SBATCH --nodes 1                                                                                                                                                                              
#SBATCH --ntasks 48                                                                                                                                                                            
#SBATCH --output /scratch/07804/bsaakash/tapis/REU_2024/job.out                                                                                           
#SBATCH --partition skx                                                                                                                                                                        
#SBATCH --time 660          

runjob.sh
