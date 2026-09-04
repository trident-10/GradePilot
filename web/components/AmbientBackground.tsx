/** Pure CSS ambient atmosphere. No JS animation loops. */
export function AmbientBackground() {
  return (
    <div className="gp-ambient" aria-hidden>
      <div className="gp-ambient-orb gp-ambient-orb-a" />
      <div className="gp-ambient-orb gp-ambient-orb-b" />
      <div className="gp-ambient-orb gp-ambient-orb-c md:block hidden" />
    </div>
  );
}
