        # Treeview per i core
        self.cores_tree = ttk.Treeview(cores_frame, columns=("platform", "core"), show="headings", height=15)
        self.cores_tree.heading("platform", text="Piattaforma")
        self.cores_tree.heading("core", text="Core (.dll)")
        self.cores_tree.column("platform", width=200)
        self.cores_tree.column("core", width=300)
        self.cores_tree.pack(fill="both", expand=True, padx=5, pady=5)