# SLURM specifications made in default.cluster.yaml & the individual rules
# GRB_LICENSE_FILE=/share/software/user/restricted/gurobi/11.0.2/licenses/gurobi.lic⁠
snakemake --cluster "sbatch -A {cluster.account} --mail-type ALL --mail-user {cluster.email}  -p {cluster.partition} -o {cluster.output} -e {cluster.error} -c {threads} --mem {cluster.mem} --time {cluster.walltime}" --cluster-config config/config.cluster.yaml --rerun-triggers mtime -R build_cutout --jobs 5 --latency-wait 60 --ignore-incomplete --configfile config/config.energymet_1988.yaml --resources concurrent_resources=2
