// The "answer capsule" — a 40–60 word BLUF that an AI engine can lift verbatim.
// Rendered high in the page, visually distinct, in plain factual prose.
export default function AnswerCapsule({ text }: { text: string }) {
  return (
    <div className="capsule" role="note">
      <p className="capsule__label">Quick answer</p>
      <p className="capsule__text">{text}</p>
    </div>
  );
}
