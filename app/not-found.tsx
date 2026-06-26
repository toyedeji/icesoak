import Link from "next/link";

export default function NotFound() {
  return (
    <div className="wrap">
      <h1>Page not found</h1>
      <p className="lead">
        That page doesn&apos;t exist or hasn&apos;t been published yet.
      </p>
      <p>
        <Link href="/">Go to the IceSoak home page</Link> or browse the{" "}
        <Link href="/guides/">guides</Link>.
      </p>
    </div>
  );
}
