import NewProjectCard from "./NewProjectCard";

export default function StartNewProject() {
  return (
    <section className="mb-12">
      <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-brand-green)' }}>
        Start a new project
      </h2>
      <div className="flex justify gap-4">
        <NewProjectCard
          title="Blank Space"
          to="/workshop?id=blank"
        />
        {/* <NewProjectCard
          title="Rumah Alvin"
          to="/workshop"
        />
        <NewProjectCard
          title="Rumah Budhi"
          to="/workshop"
        />
        <NewProjectCard
          title="Rumah Raymond"
          to="/workshop"
        /> */}
      </div>
    </section>
  );
}
