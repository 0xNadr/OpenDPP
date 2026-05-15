import { expect } from "chai";
import { ethers } from "hardhat";
import { keccak256, toUtf8Bytes } from "ethers";

describe("OpenDPPAnchor", () => {
  async function deploy() {
    const Factory = await ethers.getContractFactory("OpenDPPAnchor");
    const c = await Factory.deploy();
    await c.waitForDeployment();
    return c;
  }

  it("anchors a fresh hash and records the timestamp", async () => {
    const c = await deploy();
    const hash = keccak256(toUtf8Bytes("snapshot-1"));

    await expect(c.anchor(hash))
      .to.emit(c, "Anchored")
      .withArgs(hash, (await ethers.provider.getSigner()).address, (n: bigint) => n > 0n);

    const recorded = await c.anchoredAt(hash);
    expect(recorded).to.be.gt(0);
  });

  it("returns 0 for unanchored hashes", async () => {
    const c = await deploy();
    expect(await c.anchoredAt(keccak256(toUtf8Bytes("never")))).to.equal(0n);
  });

  it("rejects re-anchoring the same hash", async () => {
    const c = await deploy();
    const hash = keccak256(toUtf8Bytes("snapshot-1"));
    await c.anchor(hash);
    await expect(c.anchor(hash)).to.be.revertedWith("OpenDPPAnchor: already anchored");
  });

  it("anchorBatch records all hashes", async () => {
    const c = await deploy();
    const hashes = [
      keccak256(toUtf8Bytes("h1")),
      keccak256(toUtf8Bytes("h2")),
      keccak256(toUtf8Bytes("h3")),
    ];
    await c.anchorBatch(hashes);
    for (const h of hashes) {
      expect(await c.anchoredAt(h)).to.be.gt(0);
    }
  });
});
