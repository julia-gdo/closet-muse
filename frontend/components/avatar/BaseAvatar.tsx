import Image from "next/image";

export function BaseAvatar({ className }: { className?: string }) {
  return (
    <div className={className}>
      <Image
        src="/assets/avatar/base.png"
        alt="Your avatar"
        width={333}
        height={749}
        className="h-full w-full object-contain"
        priority
      />
    </div>
  );
}
